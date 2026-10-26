from types import SimpleNamespace

from app.main import app
from app.oauth2 import get_current_user


def test_bid_on_nonexistent_product(client):
    fake_user = SimpleNamespace(id=100)

    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        response = client.post(
            "/bids/999999",
            json={"amount": 600},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == ("Product with id 999999 not found")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
