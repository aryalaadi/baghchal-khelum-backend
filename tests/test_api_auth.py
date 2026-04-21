from app.db.models.password_reset_code import PasswordResetCode


def test_register_login_and_policy_paths(client):
    ok = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "StrongPass1"},
    )
    assert ok.status_code == 200
    assert "token" in ok.json()

    dup_user = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice2@example.com", "password": "StrongPass1"},
    )
    assert dup_user.status_code == 400

    bad_email = client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "email": "bad", "password": "StrongPass1"},
    )
    assert bad_email.status_code == 400

    weak_pw = client.post(
        "/api/v1/auth/register",
        json={"username": "charlie", "email": "charlie@example.com", "password": "weak"},
    )
    assert weak_pw.status_code == 400

    login_ok = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "StrongPass1"},
    )
    assert login_ok.status_code == 200

    login_bad_user = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "StrongPass1"},
    )
    assert login_bad_user.status_code == 401

    login_bad_pw = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "WrongPass1"},
    )
    assert login_bad_pw.status_code == 401


def test_forgot_password_flow(client, db_session, monkeypatch):
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "resetuser", "email": "reset@example.com", "password": "StrongPass1"},
    )
    assert register.status_code == 200

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.send_reset_code_email",
        lambda *_args, **_kwargs: (True, "sent"),
    )

    req = client.post("/api/v1/auth/forgot-password/request", json={"email": "reset@example.com"})
    assert req.status_code == 200

    code_row = db_session.query(PasswordResetCode).first()
    assert code_row is not None

    verify = client.post(
        "/api/v1/auth/forgot-password/verify",
        json={
            "email": "reset@example.com",
            "code": code_row.code,
            "new_password": "NewStrong1",
        },
    )
    assert verify.status_code == 200

    login_new = client.post(
        "/api/v1/auth/login",
        json={"username": "resetuser", "password": "NewStrong1"},
    )
    assert login_new.status_code == 200
