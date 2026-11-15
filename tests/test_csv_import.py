"""CSV import: the upload is checked and queued, a worker imports it, and the owner
polls the task.

Celery runs eagerly here, so the result is ready right after the POST. The task shares
the test's one connection, and its savepoint sits inside the request's, so the request
closing rolls the import back. Tests that look at the database therefore call the task
directly; the HTTP tests check what the endpoints answer."""

import pytest

from app import models
from app.worker import tasks

HEADER = "name,description,start_price\n"


def upload(client, headers, content: bytes, filename: str = "products.csv"):
    return client.post(
        "/products/import-csv",
        headers=headers,
        files={"file": (filename, content, "text/csv")},
    )


def run_import(client, headers, content: bytes):
    """Queue an import and return the status endpoint's answer."""
    queued = upload(client, headers, content)
    assert queued.status_code == 202, queued.text
    result = client.get(
        f"/products/import-csv/{queued.json()['task_id']}", headers=headers
    )
    assert result.status_code == 200, result.text
    return result.json()


def count_products(db_session, user):
    return db_session.query(models.Product).filter_by(owner_id=user.id).count()


def test_valid_csv_is_queued_and_the_status_endpoint_reports_success(
    client, make_user, auth, eager_celery
):
    content = f"{HEADER}Camera,New,100\nLaptop,Used,250\n".encode()

    body = run_import(client, auth(make_user()), content)

    assert body["status"] == "success"
    assert body["imported_count"] == 2


def test_task_imports_draft_products_owned_by_the_uploader(
    db_session, task_sessions, make_user
):
    user = make_user()

    result = tasks.import_products_csv_task(
        f"{HEADER}Camera,New,100\nLaptop,Used,250\n", user.id
    )

    assert result["status"] == "success"
    assert result["imported_count"] == 2
    products = db_session.query(models.Product).filter_by(owner_id=user.id).all()
    assert {p.name for p in products} == {"Camera", "Laptop"}
    assert all(p.status.value == "draft" for p in products)
    assert all(p.current_price == p.start_price for p in products)


def test_the_upload_is_queued_with_the_text_and_the_owner(
    client, make_user, auth, monkeypatch
):
    user = make_user()
    queued = {}

    def fake_apply_async(args, task_id):
        queued.update(args=args, task_id=task_id)

    monkeypatch.setattr(tasks.import_products_csv_task, "apply_async", fake_apply_async)
    content = f"{HEADER}A,B,100\n".encode()

    response = upload(client, auth(user), content)

    assert response.status_code == 202
    assert response.json() == {"task_id": queued["task_id"]}
    assert queued["args"] == [content.decode(), user.id]
    assert queued["task_id"].startswith(f"csv-{user.id}-")


@pytest.mark.parametrize(
    "filename,content,expected",
    [
        ("products.txt", f"{HEADER}A,B,100\n".encode(), 400),
        ("products.csv", b"\xff\xfe", 400),
        ("products.csv", HEADER.encode() + b"A" * (2 * 1024 * 1024), 413),
    ],
)
def test_bad_uploads_are_refused_before_anything_is_queued(
    client, make_user, auth, monkeypatch, filename, content, expected
):
    queued = []
    monkeypatch.setattr(
        tasks.import_products_csv_task, "apply_async", lambda **kw: queued.append(kw)
    )

    response = upload(client, auth(make_user()), content, filename)

    assert response.status_code == expected, response.text
    assert queued == []


@pytest.mark.parametrize(
    "text",
    ["wrong,description,start_price\nA,B,100\n", HEADER],
)
def test_wrong_header_or_no_rows_fails_the_task(
    db_session, task_sessions, make_user, text
):
    user = make_user()

    result = tasks.import_products_csv_task(text, user.id)

    assert result["status"] == "failed"
    assert isinstance(result["detail"], str)
    assert count_products(db_session, user) == 0


@pytest.mark.parametrize(
    "rows,bad_rows",
    [
        ("A,B,0\n", [2]),
        ("A,B,100\nC,D,-5\n", [3]),
        ("A,B,100,EXTRA\n", [2]),
        ("A,B,0\nC,D,-5\n", [2, 3]),
    ],
)
def test_bad_rows_fail_the_whole_import_and_name_the_rows(
    db_session, task_sessions, make_user, rows, bad_rows
):
    user = make_user()

    result = tasks.import_products_csv_task(HEADER + rows, user.id)

    assert result["status"] == "failed"
    assert [e["row"] for e in result["detail"]["errors"]] == bad_rows
    assert count_products(db_session, user) == 0  # all or nothing


def test_a_business_failure_is_reported_through_the_status_endpoint(
    client, make_user, auth, eager_celery
):
    body = run_import(client, auth(make_user()), f"{HEADER}A,B,0\n".encode())

    # Celery calls this task SUCCESS because it returned; the body says it failed.
    assert body["status"] == "failed"
    assert body["detail"]["errors"][0]["row"] == 2


def test_requires_authentication(client):
    assert upload(client, {}, f"{HEADER}A,B,100\n".encode()).status_code == 401
    assert client.get("/products/import-csv/csv-1-x").status_code == 401


def test_status_of_another_users_task_is_not_found(
    client, make_user, auth, eager_celery
):
    owner, other = make_user(), make_user()
    queued = upload(client, auth(owner), f"{HEADER}A,B,100\n".encode())

    response = client.get(
        f"/products/import-csv/{queued.json()['task_id']}", headers=auth(other)
    )

    assert response.status_code == 404


def test_status_of_a_made_up_task_id_is_not_found(client, make_user, auth):
    response = client.get("/products/import-csv/not-a-task", headers=auth(make_user()))

    assert response.status_code == 404


def test_pending_task_reports_processing(client, make_user, auth, monkeypatch):
    user = make_user()
    monkeypatch.setattr(
        tasks.import_products_csv_task, "apply_async", lambda **kw: None
    )
    queued = upload(client, auth(user), f"{HEADER}A,B,100\n".encode())

    response = client.get(
        f"/products/import-csv/{queued.json()['task_id']}", headers=auth(user)
    )

    assert response.json() == {"status": "processing"}


def test_a_crashed_task_reports_a_generic_error(
    client, make_user, auth, eager_celery, monkeypatch
):
    def explode(**kwargs):
        raise RuntimeError("secret database detail")

    monkeypatch.setattr(tasks, "import_products_from_text", explode)
    user = make_user()
    eager_celery.conf.task_eager_propagates = False

    body = run_import(client, auth(user), f"{HEADER}A,B,100\n".encode())

    assert body == {"status": "error", "detail": "Import failed unexpectedly."}
    assert "secret" not in str(body)
