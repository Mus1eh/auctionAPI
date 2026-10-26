import pytest
from app import models


def upload(client, user, auth, content, filename='products.csv'):
    return client.post('/products/import-csv', headers=auth(user), files={
        'file': (filename, content, 'text/csv')})


def test_import_valid_csv(client, db_session, make_user, auth):
    user = make_user()
    csv = b'name,description,start_price\nCamera,New,100\nLaptop,Used,250\n'
    response = upload(client, user, auth, csv)
    assert response.status_code == 201, response.text
    assert response.json()['imported_count'] == 2
    assert db_session.query(models.Product).filter_by(owner_id=user.id).count() == 2


@pytest.mark.parametrize('filename,content,expected', [
    ('products.txt', b'name,description,start_price\nA,B,100\n', 400),
    ('products.csv', b'wrong,description,start_price\nA,B,100\n', 400),
    ('products.csv', b'name,description,start_price\n', 400),
    ('products.csv', b'\xff\xfe', 400),
    ('products.csv', b'name,description,start_price\nA,B,0\n', 422),
    ('products.csv', b'name,description,start_price\nA,B,100\nC,D,-5\n', 422),
    ('products.csv', b'name,description,start_price\nA,B,100,EXTRA\n', 422),
])
def test_import_invalid_csv(client, db_session, make_user, auth, filename, content, expected):
    user = make_user()
    response = upload(client, user, auth, content, filename)
    assert response.status_code == expected, response.text
    assert db_session.query(models.Product).filter_by(owner_id=user.id).count() == 0


def test_import_file_too_large(client, make_user, auth):
    user = make_user()
    content = b'name,description,start_price\n' + b'A' * (2 * 1024 * 1024)
    assert upload(client, user, auth, content).status_code == 413


def test_import_requires_authentication(client):
    response = client.post('/products/import-csv', files={'file': ('test.csv', b'name,description,start_price\nA,B,100', 'text/csv')})
    assert response.status_code == 401
