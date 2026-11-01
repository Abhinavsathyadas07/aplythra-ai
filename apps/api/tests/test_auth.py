from collections.abc import Callable
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from tests.conftest import auth


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_garbage_token_rejected(client: TestClient) -> None:
    assert client.get("/me", headers=auth("not.a.jwt")).status_code == 401


def test_expired_token_rejected(client: TestClient, make_token: Callable[..., str]) -> None:
    assert client.get("/me", headers=auth(make_token(expires_in=-10))).status_code == 401


def test_wrong_audience_rejected(client: TestClient, make_token: Callable[..., str]) -> None:
    assert client.get("/me", headers=auth(make_token(audience="anon"))).status_code == 401


def test_wrong_issuer_rejected(client: TestClient, make_token: Callable[..., str]) -> None:
    assert (
        client.get("/me", headers=auth(make_token(issuer="https://evil.example"))).status_code
        == 401
    )


def test_token_signed_with_other_key_rejected(
    client: TestClient, make_token: Callable[..., str]
) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert client.get("/me", headers=auth(make_token(key=other))).status_code == 401


def test_non_uuid_subject_rejected(client: TestClient, make_token: Callable[..., str]) -> None:
    assert client.get("/me", headers=auth(make_token(sub="not-a-uuid"))).status_code == 401


def test_hs256_token_rejected(client: TestClient) -> None:
    import jwt

    forged = jwt.encode(
        {"sub": str(uuid4()), "aud": "authenticated", "exp": 9999999999},
        "x" * 32,
        algorithm="HS256",
    )
    assert client.get("/me", headers=auth(forged)).status_code == 401


def test_error_body_does_not_echo_token(client: TestClient) -> None:
    response = client.get("/me", headers=auth("secret.token.value"))
    assert "secret.token.value" not in response.text
