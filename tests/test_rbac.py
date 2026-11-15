"""Roles and permissions: access follows permissions, not role names, and superadmin
bypasses the check."""

import pytest
from sqlalchemy import event

from app import models
from app.core.policies import has_permission
from app.seeders.rbac import PERMISSIONS, ROLE_PERMISSIONS


def role(db_session, name: str) -> models.Role:
    return db_session.query(models.Role).filter_by(name=name).one()


def dashboard(client, auth, user):
    return client.get("/admin/dashboard", headers=auth(user))


# --- the seeded roles ---------------------------------------------------------


def test_every_role_permission_exists():
    for permissions in ROLE_PERMISSIONS.values():
        assert set(permissions) <= set(PERMISSIONS)


def test_roles_hold_exactly_their_seeded_permissions(db_session, roles):
    for name, expected in ROLE_PERMISSIONS.items():
        assert {p.name for p in role(db_session, name).permissions} == set(expected)


def test_ordinary_users_hold_no_permissions(make_user):
    user = make_user()

    assert not any(has_permission(user, name) for name in PERMISSIONS)


def test_admins_cannot_assign_roles_or_delete_admins(make_user):
    admin = make_user("admin")

    assert not has_permission(admin, "user.role.assign")
    assert not has_permission(admin, "user.role.remove")
    assert not has_permission(admin, "user.delete_admin")


# --- enforcement --------------------------------------------------------------


def test_permission_gates_the_admin_router(client, make_user, auth):
    assert dashboard(client, auth, make_user()).status_code == 403
    assert dashboard(client, auth, make_user("admin")).status_code == 200


def test_access_follows_the_permission_not_the_role_name(
    client, db_session, make_user, auth
):
    admin = make_user("admin")
    admin_role = role(db_session, "admin")
    access = next(p for p in admin_role.permissions if p.name == "admin.access")

    admin_role.permissions.remove(access)
    db_session.flush()
    db_session.expire_all()

    assert dashboard(client, auth, admin).status_code == 403


def test_a_permission_added_to_a_role_takes_effect(client, db_session, make_user, auth):
    user = make_user()
    assert dashboard(client, auth, user).status_code == 403

    access = db_session.query(models.Permission).filter_by(name="admin.access").one()
    role(db_session, "user").permissions.append(access)
    db_session.flush()
    db_session.expire_all()

    assert dashboard(client, auth, user).status_code == 200


def test_superadmin_bypasses_even_with_no_permissions(
    client, db_session, make_user, auth
):
    superadmin = make_user("superadmin")
    role(db_session, "superadmin").permissions = []
    db_session.flush()
    db_session.expire_all()

    assert dashboard(client, auth, superadmin).status_code == 200
    assert has_permission(superadmin, "user.delete_admin")


def test_permissions_of_all_roles_add_up(db_session, make_user):
    user = make_user()
    user.roles.append(role(db_session, "admin"))
    db_session.flush()

    assert has_permission(user, "admin.access")
    assert not has_permission(user, "user.role.assign")


def test_a_role_name_alone_is_not_enough(client, db_session, make_user, auth):
    # A role called "admin" that holds no permissions opens nothing.
    user = make_user()
    user.roles = [role(db_session, "admin")]
    role(db_session, "admin").permissions = []
    db_session.flush()
    db_session.expire_all()

    assert dashboard(client, auth, user).status_code == 403


@pytest.mark.parametrize("who,expected", [("user", 403), ("admin", 200)])
def test_viewing_another_users_profile_needs_user_view_any(
    client, make_user, auth, who, expected
):
    target = make_user()

    response = client.get(f"/users/{target.id}", headers=auth(make_user(who)))

    assert response.status_code == expected


def test_a_user_can_always_view_themselves(client, make_user, auth):
    user = make_user()

    assert client.get(f"/users/{user.id}", headers=auth(user)).status_code == 200


# --- queries ------------------------------------------------------------------


def count_selects(db_session, request):
    statements = []

    def record(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    engine = db_session.get_bind().engine
    event.listen(engine, "before_cursor_execute", record)
    try:
        request()
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return len(statements)


def test_loading_roles_and_permissions_does_not_scale_with_their_number(
    client, db_session, make_user, auth
):
    one_role = make_user("user")
    many_roles = make_user("admin")
    many_roles.roles.append(role(db_session, "superadmin"))
    db_session.flush()
    db_session.expire_all()

    few = count_selects(db_session, lambda: dashboard(client, auth, one_role))
    many = count_selects(db_session, lambda: dashboard(client, auth, many_roles))

    # No N+1: a user with more roles and permissions costs the same number of queries.
    assert many == few
