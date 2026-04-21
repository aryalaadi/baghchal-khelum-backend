from datetime import datetime, timezone

from app.db.models.community import Post
from app.db.models.friend_challenge import ChallengeStatus, FriendChallenge
from app.db.models.game_log import GameLog
from app.db.models.replay import Replay


def test_users_community_and_replay_endpoints(client, db_session, make_user):
    u1 = make_user("u1", "u1@example.com", elo=1400)
    u2 = make_user("u2", "u2@example.com", elo=1300)

    db_session.add(Post(user_id=u1.id, title="hello", content="world"))
    db_session.add(
        Replay(
            game_id="g-1",
            player1_id=u1.id,
            player2_id=u2.id,
            winner_id=u1.id,
            moves=[{"type": "place", "position": 6}],
        )
    )
    db_session.add(
        GameLog(
            match_id="m-1",
            tiger_player_id=u2.id,
            goat_player_id=u1.id,
            winner_id=u2.id,
            result="tiger_win",
            goats_captured=5,
            total_moves=12,
            game_duration_seconds=60,
            tiger_elo_before=1300,
            tiger_elo_after=1310,
            goat_elo_before=1400,
            goat_elo_after=1390,
        )
    )
    db_session.commit()

    all_users = client.get("/api/v1/users/all")
    assert all_users.status_code == 200
    assert len(all_users.json()) >= 2

    profile = client.get(f"/api/v1/users/{u1.id}")
    assert profile.status_code == 200
    assert profile.json()["stats"]["games_played"] >= 0

    stats = client.get(f"/api/v1/users/{u1.id}/stats")
    assert stats.status_code == 200

    games = client.get(f"/api/v1/users/{u1.id}/games")
    assert games.status_code == 200
    assert len(games.json()) == 1

    leaderboard = client.get("/api/v1/community/leaderboard")
    assert leaderboard.status_code == 200
    assert "users" in leaderboard.json()

    feed = client.get("/api/v1/community/feed")
    assert feed.status_code == 200
    assert len(feed.json()) == 1

    replay = client.get("/api/v1/replay/g-1")
    assert replay.status_code == 200
    payload = replay.json()
    assert payload["moves"][0]["type"] == "place"
    assert payload["game_data"]["moves"][0]["type"] == "place"

    replay_list = client.get(f"/api/v1/replay/user/{u1.id}")
    assert replay_list.status_code == 200
    assert replay_list.json()[0]["game_id"] == "g-1"


def test_community_create_post_requires_valid_token(client, db_session, make_user, auth_header_for):
    user = make_user("poster", "poster@example.com")
    headers = auth_header_for(user.id, user.username)

    ok = client.post(
        "/api/v1/community/post",
        headers=headers,
        json={"title": "A", "content": "B"},
    )
    assert ok.status_code == 200

    bad = client.post(
        "/api/v1/community/post",
        headers={"Authorization": "Bearer broken"},
        json={"title": "A", "content": "B"},
    )
    assert bad.status_code == 401


def test_friend_and_challenge_endpoints(client, db_session, make_user, auth_header_for, monkeypatch):
    u1 = make_user("friend1", "friend1@example.com")
    u2 = make_user("friend2", "friend2@example.com")
    headers = auth_header_for(u1.id, u1.username)

    add = client.post("/api/v1/friends/add", headers=headers, json={"friend_id": u2.id})
    assert add.status_code == 200

    list_friends = client.get("/api/v1/friends/", headers=headers)
    assert list_friends.status_code == 200
    assert len(list_friends.json()) == 1

    challenge = client.post("/api/v1/friends/challenge", headers=headers, json={"friend_id": u2.id})
    assert challenge.status_code == 200

    headers_u2 = auth_header_for(u2.id, u2.username)
    challenges = client.get("/api/v1/friends/challenges", headers=headers_u2)
    assert challenges.status_code == 200
    challenge_id = challenges.json()[0]["id"]

    async def fake_respond(_db, _challenge_id, _user_id, accept):
        return "match-123" if accept else None

    monkeypatch.setattr("app.api.v1.endpoints.friend.friend_service.respond_to_challenge", fake_respond)

    accept = client.post(
        "/api/v1/friends/challenge/respond",
        headers=headers_u2,
        json={"challenge_id": challenge_id, "action": "accept"},
    )
    assert accept.status_code == 200
    assert accept.json()["match_id"] == "match-123"

    remove = client.delete(f"/api/v1/friends/{u2.id}", headers=headers)
    assert remove.status_code == 200


def test_matchmaking_endpoints(client, make_user, auth_header_for, monkeypatch):
    user = make_user("mm", "mm@example.com")
    headers = auth_header_for(user.id, user.username)

    async def fake_add(_user_id):
        return None

    async def fake_remove(_user_id):
        return None

    async def fake_heartbeat(_user_id):
        return None

    class FakeRedis:
        async def lrange(self, *_args, **_kwargs):
            return []

        async def get(self, *_args, **_kwargs):
            return None

    async def fake_get_redis():
        return FakeRedis()

    monkeypatch.setattr("app.api.v1.endpoints.matchmaking.add_to_queue", fake_add)
    monkeypatch.setattr("app.api.v1.endpoints.matchmaking.remove_from_queue", fake_remove)
    monkeypatch.setattr("app.services.matchmaking_service.heartbeat_user", fake_heartbeat)
    monkeypatch.setattr("app.core.redis.get_redis", fake_get_redis)

    start = client.post("/api/v1/matchmaking/start", headers=headers)
    assert start.status_code == 200
    assert start.json()["status"] == "queued"

    heartbeat = client.post("/api/v1/matchmaking/heartbeat", headers=headers)
    assert heartbeat.status_code == 200

    status = client.get("/api/v1/matchmaking/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "waiting"

    cancel = client.post("/api/v1/matchmaking/cancel", headers=headers)
    assert cancel.status_code == 200


def test_ai_move_endpoint_validation(client, make_user, auth_header_for, monkeypatch):
    user = make_user("aiu", "aiu@example.com")
    headers = auth_header_for(user.id, user.username)

    class FakeAI:
        def choose_move(self, **_kwargs):
            return ({"type": "place", "position": 6}, "hybrid", 1.0)

    monkeypatch.setattr("app.api.v1.endpoints.game.hybrid_ai_service", FakeAI())

    ok = client.post(
        "/api/v1/game/ai/move",
        headers=headers,
        json={
            "board": [0] * 25,
            "turn": "goat",
            "phase": 1,
            "goats_placed": 0,
            "goats_captured": 0,
            "ai_role": "goat",
            "mode": "hybrid",
            "top_k": 3,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["move_type"] == "place"

    bad = client.post(
        "/api/v1/game/ai/move",
        headers=headers,
        json={
            "board": [0] * 24,
            "turn": "goat",
            "phase": 1,
            "goats_placed": 0,
            "goats_captured": 0,
        },
    )
    assert bad.status_code == 400


def test_admin_routes(client, db_session, make_user):
    make_user("admin-user", "admin-user@example.com")

    login_page = client.get("/admin")
    assert login_page.status_code == 200

    bad = client.post("/admin/login", data={"secret": "wrong"})
    assert bad.status_code == 401

    good = client.post("/admin/login", data={"secret": "change-me-admin-secret"}, follow_redirects=False)
    assert good.status_code == 302

    cookie = good.cookies.get("admin_auth")
    assert cookie == "change-me-admin-secret"

    dashboard = client.get("/admin/dashboard", cookies={"admin_auth": cookie})
    assert dashboard.status_code == 200

    create = client.post(
        "/admin/users/create",
        cookies={"admin_auth": cookie},
        data={
            "username": "newadminuser",
            "email": "newadminuser@example.com",
            "password": "StrongPass1",
            "elo_rating": 1200,
        },
        follow_redirects=False,
    )
    assert create.status_code == 302
