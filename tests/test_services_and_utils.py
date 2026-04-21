import asyncio

import pytest

from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.services import auth_service, email_service, elo_service, game_log_service, replay_service
from app.services.game.game_service import BaghChalGame, GOAT, TIGER


def test_security_hash_and_token_roundtrip():
    hashed = get_password_hash("StrongPass1")
    assert verify_password("StrongPass1", hashed)
    assert not verify_password("WrongPass1", hashed)

    token = create_access_token({"sub": "123", "username": "tester"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "123"


@pytest.mark.parametrize(
    "email,expected",
    [
        ("a@b.com", True),
        ("bad", False),
        ("", False),
    ],
)
def test_email_validation(email, expected):
    assert auth_service.is_valid_email(email) is expected


@pytest.mark.parametrize(
    "password,valid",
    [
        ("StrongPass1", True),
        ("short", False),
        ("nouppercase1", False),
        ("NOLOWERCASE1", False),
        ("NoNumber", False),
    ],
)
def test_password_strength(password, valid):
    err = auth_service.validate_password_strength(password)
    assert (err is None) is valid


def test_password_reset_code_normalization_and_reset(db_session, make_user):
    user = make_user("rst", "rst@example.com")
    code = auth_service.create_password_reset_code(db_session, user.id)

    fetched = auth_service.verify_password_reset_code(db_session, user.id, f" {code} ")
    assert fetched is not None

    ok = auth_service.reset_password_with_code(db_session, user, code, "NewPass11")
    assert ok is True


def test_elo_rating_update(db_session, make_user):
    winner = make_user("winner", "winner@example.com", elo=1200)
    loser = make_user("loser", "loser@example.com", elo=1200)

    result = asyncio.run(
        elo_service.update_elo_ratings(
            db=db_session,
            winner_id=winner.id,
            loser_id=loser.id,
        )
    )
    assert result is not None


def test_replay_service_upsert_and_fetch(db_session, make_user):
    u1 = make_user("rp1", "rp1@example.com")
    u2 = make_user("rp2", "rp2@example.com")

    replay = asyncio.run(
        replay_service.save_replay(
            db=db_session,
            game_id="g-xyz",
            player1_id=u1.id,
            player2_id=u2.id,
            winner_id=u1.id,
            moves=[{"type": "place", "position": 3}],
        )
    )
    assert replay.game_id == "g-xyz"

    replay2 = asyncio.run(
        replay_service.save_replay(
            db=db_session,
            game_id="g-xyz",
            player1_id=u1.id,
            player2_id=u2.id,
            winner_id=u2.id,
            moves=[{"type": "move", "from": 0, "to": 1}],
        )
    )
    assert replay2.winner_id == u2.id

    by_id = replay_service.get_replay(db_session, "g-xyz")
    assert by_id is not None
    assert by_id.moves[0]["type"] == "move"

    user_replays = replay_service.get_user_replays(db_session, u1.id)
    assert len(user_replays) == 1


def test_game_log_service_updates_stats(db_session, make_user):
    tiger = make_user("tiger", "tiger@example.com")
    goat = make_user("goat", "goat@example.com")

    row = game_log_service.log_game(
        db=db_session,
        match_id="m-1",
        tiger_player_id=tiger.id,
        goat_player_id=goat.id,
        winner_id=tiger.id,
        result="tiger_win",
        goats_captured=5,
        total_moves=30,
        game_duration_seconds=80,
        tiger_elo_before=1200,
        tiger_elo_after=1216,
        goat_elo_before=1200,
        goat_elo_after=1184,
        moves_history={"moves": []},
    )
    assert row.id is not None

    db_session.refresh(tiger)
    db_session.refresh(goat)
    assert tiger.games_played == 1
    assert tiger.games_won == 1
    assert goat.games_lost == 1


def test_baghchal_game_core_rules():
    game = BaghChalGame()

    ok, _ = game.place_goat(6)
    assert ok is True
    assert game.board[6] == GOAT

    ok_t, _, _ = game.move_tiger(0, 1)
    assert ok_t is True
    assert game.board[1] == TIGER

    game.phase = 2
    game.turn = "goat"
    game.board[7] = GOAT
    game.board[6] = 0
    moved, _ = game.move_goat(7, 6)
    assert moved is True


def test_email_service_config_validation(monkeypatch):
    class SettingsStub:
        SMTP_HOST = ""
        SMTP_FROM_EMAIL = ""
        SMTP_USE_SSL = False
        SMTP_USE_TLS = True
        SMTP_PORT = 587
        SMTP_USERNAME = ""
        SMTP_PASSWORD = ""

    monkeypatch.setattr(email_service, "settings", SettingsStub)
    ok, reason = email_service.send_reset_code_email("a@b.com", "u", "123456")
    assert ok is False
    assert "SMTP_HOST" in reason
