from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.game_log import GameLog
from app.db.models.replay import Replay
from app.db.models.friend_challenge import FriendChallenge

router = APIRouter(tags=["admin"])


def _is_admin_authenticated(request: Request) -> bool:
    cookie_value = request.cookies.get("admin_auth")
    return bool(cookie_value and cookie_value == settings.ADMIN_PANEL_SECRET)


@router.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    if _is_admin_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=302)

    return HTMLResponse(
        """
        <html>
          <head><title>Admin Login</title></head>
          <body style="font-family: Arial; max-width: 420px; margin: 60px auto;">
            <h2>Baghchal Admin</h2>
            <form method="post" action="/admin/login">
              <label>Admin Secret</label><br/>
              <input type="password" name="secret" style="width:100%;padding:10px;margin:12px 0;" required/>
              <button type="submit" style="padding:10px 16px;">Login</button>
            </form>
          </body>
        </html>
        """
    )


@router.post("/admin/login")
def admin_login(secret: str = Form(...)):
    if secret != settings.ADMIN_PANEL_SECRET:
        return HTMLResponse("<h3>Invalid admin secret</h3><a href='/admin'>Back</a>", status_code=401)

    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="admin_auth",
        value=settings.ADMIN_PANEL_SECRET,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return response


@router.get("/admin/logout")
def admin_logout():
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("admin_auth")
    return response


@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    users_count = db.query(User).count()
    game_logs_count = db.query(GameLog).count()
    replays_count = db.query(Replay).count()
    challenges_count = db.query(FriendChallenge).count()

    latest_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    latest_games = db.query(GameLog).order_by(GameLog.created_at.desc()).limit(10).all()

    users_rows = "".join(
        f"<tr><td>{u.id}</td><td>{u.username}</td><td>{u.email or '-'}</td><td>{u.elo_rating:.1f}</td></tr>"
        for u in latest_users
    )
    games_rows = "".join(
        f"<tr><td>{g.id}</td><td>{g.match_id}</td><td>{g.result}</td><td>{g.total_moves}</td></tr>"
        for g in latest_games
    )

    html = f"""
    <html>
      <head><title>Admin Dashboard</title></head>
      <body style='font-family: Arial; max-width: 1100px; margin: 30px auto;'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
          <h2>Baghchal Admin Dashboard</h2>
          <a href='/admin/logout'>Logout</a>
        </div>
        <div style='display:grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0;'>
          <div style='padding:12px;border:1px solid #ddd;'>Users: <b>{users_count}</b></div>
          <div style='padding:12px;border:1px solid #ddd;'>Game Logs: <b>{game_logs_count}</b></div>
          <div style='padding:12px;border:1px solid #ddd;'>Replays: <b>{replays_count}</b></div>
          <div style='padding:12px;border:1px solid #ddd;'>Challenges: <b>{challenges_count}</b></div>
        </div>

        <h3>Latest Users</h3>
        <table border='1' cellpadding='8' cellspacing='0' width='100%'>
          <tr><th>ID</th><th>Username</th><th>Email</th><th>ELO</th></tr>
          {users_rows}
        </table>

        <h3 style='margin-top:24px;'>Latest Games</h3>
        <table border='1' cellpadding='8' cellspacing='0' width='100%'>
          <tr><th>ID</th><th>Match ID</th><th>Result</th><th>Total Moves</th></tr>
          {games_rows}
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)
