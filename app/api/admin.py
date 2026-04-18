from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, delete
import html
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.user import friends_association
from app.db.models.game_log import GameLog
from app.db.models.replay import Replay
from app.db.models.friend_challenge import FriendChallenge
from app.db.models.community import Post
from app.db.models.password_reset_code import PasswordResetCode
from app.services.auth_service import is_valid_email, validate_password_strength

router = APIRouter(tags=["admin"])


def _is_admin_authenticated(request: Request) -> bool:
    cookie_value = request.cookies.get("admin_auth")
    return bool(cookie_value and cookie_value == settings.ADMIN_PANEL_SECRET)


def _admin_page_wrapper(title: str, body_html: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
        <html>
          <head>
            <title>{title}</title>
            <style>
              :root {{
                --bg: #0f172a;
                --panel: #111827;
                --panel-2: #1f2937;
                --text: #e5e7eb;
                --muted: #9ca3af;
                --accent: #22c55e;
                --danger: #ef4444;
                --border: #374151;
              }}
              * {{ box-sizing: border-box; }}
              body {{ margin: 0; font-family: Inter, system-ui, Arial, sans-serif; background: var(--bg); color: var(--text); }}
              .container {{ max-width: 1240px; margin: 24px auto; padding: 0 16px; }}
              .topbar {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }}
              .nav a {{ color: var(--text); text-decoration: none; margin-right: 12px; font-size: 14px; }}
              .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px; }}
              .grid {{ display: grid; gap: 12px; }}
              .stats {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
              .small {{ color: var(--muted); font-size: 12px; }}
              input, select {{ width: 100%; background: #0b1220; border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 9px; }}
              button {{ border: none; border-radius: 8px; padding: 8px 12px; cursor: pointer; color: #fff; background: #2563eb; }}
              button.secondary {{ background: #374151; }}
              button.success {{ background: var(--accent); color: #08120b; font-weight: 600; }}
              button.danger {{ background: var(--danger); }}
              .btn {{ display: inline-block; text-decoration: none; border: none; border-radius: 8px; padding: 8px 12px; cursor: pointer; color: #fff; background: #2563eb; font-size: 13px; }}
              .btn.secondary {{ background: #374151; }}
              .btn.danger {{ background: var(--danger); }}
              table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
              th, td {{ border-bottom: 1px solid var(--border); padding: 8px 6px; text-align: left; vertical-align: top; }}
              th {{ color: var(--muted); font-weight: 600; }}
              .row {{ display: flex; gap: 8px; align-items: center; }}
              .row > * {{ flex: 1; }}
              .row.auto > * {{ flex: 0 0 auto; }}
              .row.auto .grow {{ flex: 1 1 auto; }}
              .mt {{ margin-top: 12px; }}
              .message {{ margin: 10px 0; padding: 10px; border-radius: 8px; background: #052e1d; border: 1px solid #065f46; }}
              .error {{ background: #3f0f14; border-color: #7f1d1d; }}
              @media (max-width: 980px) {{ .stats {{ grid-template-columns: 1fr 1fr; }} }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="topbar">
                <div>
                  <h2 style="margin:0 0 6px 0;">Baghchal Admin</h2>
                  <div class="nav">
                    <a href="/admin/dashboard">Dashboard</a>
                    <a href="/admin/users">Users</a>
                    <a href="/admin/logout">Logout</a>
                  </div>
                </div>
              </div>
              {body_html}
            </div>
          </body>
        </html>
        """
    )


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

    return _admin_page_wrapper(
        "Admin Dashboard",
        f"""
        <div class='grid stats'>
          <div class='card'><div class='small'>Users</div><div style='font-size:26px;font-weight:700'>{users_count}</div></div>
          <div class='card'><div class='small'>Game Logs</div><div style='font-size:26px;font-weight:700'>{game_logs_count}</div></div>
          <div class='card'><div class='small'>Replays</div><div style='font-size:26px;font-weight:700'>{replays_count}</div></div>
          <div class='card'><div class='small'>Challenges</div><div style='font-size:26px;font-weight:700'>{challenges_count}</div></div>
        </div>

        <div class='card mt'>
          <div class='row' style='justify-content:space-between'>
            <h3 style='margin:0'>Latest Users</h3>
            <a href='/admin/users' style='color:#93c5fd'>Manage users →</a>
          </div>
          <table>
            <tr><th>ID</th><th>Username</th><th>Email</th><th>ELO</th></tr>
            {users_rows}
          </table>
        </div>

        <div class='card mt'>
          <h3 style='margin-top:0'>Latest Games</h3>
          <table>
            <tr><th>ID</th><th>Match ID</th><th>Result</th><th>Total Moves</th></tr>
            {games_rows}
          </table>
        </div>
        """,
    )


@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    q: str = "",
    min_elo: float | None = None,
    max_elo: float | None = None,
    sort_by: str = "id",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    query = db.query(User)

    if q:
        filters = [
            User.username.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
        ]
        if q.isdigit():
            filters.append(User.id == int(q))
        query = query.filter(or_(*filters))

    if min_elo is not None:
        query = query.filter(User.elo_rating >= min_elo)
    if max_elo is not None:
        query = query.filter(User.elo_rating <= max_elo)

    sort_column_map = {
        "id": User.id,
        "username": User.username,
        "email": User.email,
        "elo": User.elo_rating,
        "created": User.created_at,
        "games": User.games_played,
    }
    sort_column = sort_column_map.get(sort_by, User.id)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    users = query.limit(200).all()

    msg = request.query_params.get("msg")
    err = request.query_params.get("err")
    msg_html = f"<div class='message'>{html.escape(msg)}</div>" if msg else ""
    err_html = f"<div class='message error'>{html.escape(err)}</div>" if err else ""

    q_safe = html.escape(q)
    sort_by_safe = html.escape(sort_by)
    sort_order_safe = html.escape(sort_order)

    user_rows = []
    for user in users:
        user_rows.append(
            f"""
            <tr>
              <td>{user.id}</td>
              <td>{html.escape(user.username)}</td>
              <td>{html.escape(user.email or '-')}</td>
              <td>{user.elo_rating:.1f}</td>
              <td>{user.games_played}</td>
              <td>{user.games_won}</td>
              <td>{user.games_lost}</td>
              <td>{user.games_drawn}</td>
              <td>
                <div class='row auto'>
                  <a class='btn secondary' href='/admin/users/{user.id}/edit'>Edit</a>
                  <form method='post' action='/admin/users/{user.id}/delete' onsubmit='return confirm("Delete user #{user.id} and all related records?")' style='margin:0;'>
                    <button class='danger' type='submit'>Delete</button>
                  </form>
                </div>
              </td>
            </tr>
            """
        )

    users_html = "".join(user_rows) if user_rows else "<tr><td colspan='9'>No users found.</td></tr>"

    return _admin_page_wrapper(
        "Admin Users",
        f"""
        {msg_html}
        {err_html}

        <div class='card'>
          <h3 style='margin-top:0'>Search & Filters</h3>
          <form method='get' action='/admin/users'>
            <div class='row'>
              <input name='q' value='{q_safe}' placeholder='Search by username, email, or ID' />
              <input type='number' step='0.1' name='min_elo' placeholder='Min ELO' value='{'' if min_elo is None else min_elo}' />
              <input type='number' step='0.1' name='max_elo' placeholder='Max ELO' value='{'' if max_elo is None else max_elo}' />
              <select name='sort_by'>
                <option value='id' {'selected' if sort_by_safe == 'id' else ''}>ID</option>
                <option value='username' {'selected' if sort_by_safe == 'username' else ''}>Username</option>
                <option value='email' {'selected' if sort_by_safe == 'email' else ''}>Email</option>
                <option value='elo' {'selected' if sort_by_safe == 'elo' else ''}>ELO</option>
                <option value='created' {'selected' if sort_by_safe == 'created' else ''}>Created</option>
                <option value='games' {'selected' if sort_by_safe == 'games' else ''}>Games Played</option>
              </select>
              <select name='sort_order'>
                <option value='desc' {'selected' if sort_order_safe == 'desc' else ''}>Desc</option>
                <option value='asc' {'selected' if sort_order_safe == 'asc' else ''}>Asc</option>
              </select>
              <button type='submit'>Search</button>
              <a class='btn secondary' href='/admin/users'>Reset</a>
            </div>
          </form>
        </div>

        <div class='card mt'>
          <h3 style='margin-top:0'>Create User</h3>
          <form method='post' action='/admin/users/create'>
            <div class='row'>
              <input name='username' placeholder='username' required />
              <input name='email' placeholder='email' required />
              <input name='password' type='password' placeholder='password' required />
              <input type='number' step='0.1' name='elo_rating' value='1200' placeholder='ELO' required />
              <button class='success' type='submit'>Create</button>
            </div>
          </form>
        </div>

        <div class='card mt'>
          <h3 style='margin-top:0'>Users (max 200)</h3>
          <table>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>ELO</th>
              <th>Played</th>
              <th>Won</th>
              <th>Lost</th>
              <th>Drawn</th>
              <th>Actions</th>
            </tr>
            {users_html}
          </table>
        </div>
        """,
    )


@router.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
def admin_edit_user_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/admin/users?err=User+not+found", status_code=302)

    return _admin_page_wrapper(
        f"Edit User {user_id}",
        f"""
        <div class='card'>
          <div class='row auto' style='justify-content:space-between;margin-bottom:8px;'>
            <h3 style='margin:0'>Edit User #{user.id}</h3>
            <a class='btn secondary' href='/admin/users'>Back to Users</a>
          </div>
          <form method='post' action='/admin/users/{user.id}/update'>
            <div class='row'>
              <input name='username' value='{html.escape(user.username)}' placeholder='username' required />
              <input name='email' value='{html.escape(user.email or "")}' placeholder='email' required />
              <input type='number' step='0.1' name='elo_rating' value='{user.elo_rating}' placeholder='ELO' required />
            </div>
            <div class='row mt'>
              <input type='number' name='games_played' value='{user.games_played}' placeholder='Played' required />
              <input type='number' name='games_won' value='{user.games_won}' placeholder='Won' required />
              <input type='number' name='games_lost' value='{user.games_lost}' placeholder='Lost' required />
              <input type='number' name='games_drawn' value='{user.games_drawn}' placeholder='Drawn' required />
              <input type='number' name='goats_captured_total' value='{user.goats_captured_total}' placeholder='Goats captured' required />
            </div>
            <div class='row mt'>
              <input class='grow' name='new_password' type='password' placeholder='New password (optional)' />
            </div>
            <div class='row auto mt'>
              <button class='success' type='submit'>Save Changes</button>
            </div>
          </form>
          <form method='post' action='/admin/users/{user.id}/delete' class='mt' onsubmit='return confirm("Delete user #{user.id} and all related records?")'>
            <button class='danger' type='submit'>Delete Account</button>
          </form>
        </div>
        """,
    )


@router.post("/admin/users/create")
def admin_create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    elo_rating: float = Form(1200.0),
    db: Session = Depends(get_db),
):
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    username = username.strip()
    email = email.strip().lower()

    if not username:
        return RedirectResponse(url="/admin/users?err=Username+is+required", status_code=302)
    if not is_valid_email(email):
        return RedirectResponse(url="/admin/users?err=Invalid+email", status_code=302)
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(url="/admin/users?err=Username+already+exists", status_code=302)
    if db.query(User).filter(User.email == email).first():
        return RedirectResponse(url="/admin/users?err=Email+already+exists", status_code=302)

    password_error = validate_password_strength(password)
    if password_error:
        return RedirectResponse(url=f"/admin/users?err={password_error.replace(' ', '+')}", status_code=302)

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        elo_rating=elo_rating,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/admin/users?msg=User+created+successfully", status_code=302)


@router.post("/admin/users/{user_id}/update")
def admin_update_user(
    user_id: int,
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    elo_rating: float = Form(...),
    games_played: int = Form(...),
    games_won: int = Form(...),
    games_lost: int = Form(...),
    games_drawn: int = Form(...),
    goats_captured_total: int = Form(...),
    new_password: str = Form(""),
    db: Session = Depends(get_db),
):
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/admin/users?err=User+not+found", status_code=302)

    username = username.strip()
    email = email.strip().lower()
    if not username:
        return RedirectResponse(url="/admin/users?err=Username+is+required", status_code=302)
    if not is_valid_email(email):
        return RedirectResponse(url="/admin/users?err=Invalid+email", status_code=302)

    username_taken = db.query(User).filter(User.username == username, User.id != user_id).first()
    if username_taken:
        return RedirectResponse(url="/admin/users?err=Username+already+exists", status_code=302)

    email_taken = db.query(User).filter(User.email == email, User.id != user_id).first()
    if email_taken:
        return RedirectResponse(url="/admin/users?err=Email+already+exists", status_code=302)

    if new_password.strip():
        password_error = validate_password_strength(new_password.strip())
        if password_error:
            return RedirectResponse(url=f"/admin/users?err={password_error.replace(' ', '+')}", status_code=302)
        user.hashed_password = get_password_hash(new_password.strip())

    user.username = username
    user.email = email
    user.elo_rating = elo_rating
    user.games_played = max(0, games_played)
    user.games_won = max(0, games_won)
    user.games_lost = max(0, games_lost)
    user.games_drawn = max(0, games_drawn)
    user.goats_captured_total = max(0, goats_captured_total)

    db.commit()
    return RedirectResponse(url="/admin/users?msg=User+updated+successfully", status_code=302)


@router.post("/admin/users/{user_id}/delete")
def admin_delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not _is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/admin/users?err=User+not+found", status_code=302)

    db.query(GameLog).filter(
        or_(
            GameLog.tiger_player_id == user_id,
            GameLog.goat_player_id == user_id,
            GameLog.winner_id == user_id,
        )
    ).delete(synchronize_session=False)

    db.query(Replay).filter(
        or_(
            Replay.player1_id == user_id,
            Replay.player2_id == user_id,
            Replay.winner_id == user_id,
        )
    ).delete(synchronize_session=False)

    db.query(FriendChallenge).filter(
        or_(
            FriendChallenge.challenger_id == user_id,
            FriendChallenge.challenged_id == user_id,
        )
    ).delete(synchronize_session=False)

    db.query(Post).filter(Post.user_id == user_id).delete(synchronize_session=False)
    db.query(PasswordResetCode).filter(PasswordResetCode.user_id == user_id).delete(synchronize_session=False)

    db.execute(delete(friends_association).where(friends_association.c.user_id == user_id))
    db.execute(delete(friends_association).where(friends_association.c.friend_id == user_id))

    db.delete(user)
    db.commit()

    return RedirectResponse(url="/admin/users?msg=User+deleted+successfully", status_code=302)
