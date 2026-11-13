import os
import re
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from logic import get_response, CONDITION_NAMES

app = Flask(__name__)
# Set SECRET_KEY in your environment before deploying this app.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
DATABASE = Path(__file__).with_name("users.db")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                bot_reply TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('like', 'dislike')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender TEXT NOT NULL CHECK (sender IN ('user', 'bot')),
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        # Dashboard counts. It stores NO message text, so "Clear chat" never touches it.
        db.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('match', 'emergency', 'unclear')),
                condition_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)


init_db()

# --- Reads the bot's reply and works out what happened (used by the dashboard) ---
# Any condition name (English, Marathi or Hindi) -> its English name, so the
# dashboard counts "Migraine" and "माइग्रेन" as the same condition.
CONDITION_LOOKUP = {
    shown_name: english_name
    for english_name, names in CONDITION_NAMES.items()
    for shown_name in names
}
# Matches the "possible" line of the reply in all 3 languages
POSSIBLE_LINE = re.compile(r"(?:Possible condition|संभाव्य आजार|संभावित रोग):\s*(.+?)\s*\(")


def read_outcome(reply):
    """Returns ('match', 'Migraine'), ('emergency', None) or ('unclear', None)."""
    if reply.lstrip().startswith("🚨"):          # every emergency reply starts with this sign
        return "emergency", None
    found = POSSIBLE_LINE.search(reply)
    if found:
        shown_name = found.group(1).strip()
        return "match", CONDITION_LOOKUP.get(shown_name, shown_name)[:80]
    return "unclear", None


@app.context_processor
def inject_user():
    # Makes {{ user_name }} available in every template (the header uses it)
    return {"user_name": session.get("user_name", "User")}


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith(("/chat", "/feedback", "/history")):
                return jsonify({"error": "Please log in again."}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user_name=session.get("user_name", "User"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("Please fill in every field.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        else:
            try:
                with get_db() as db:
                    cursor = db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password))
                    )
                    user_id = cursor.lastrowid
                session.clear()
                session["user_id"] = user_id
                session["user_name"] = name
                return redirect(url_for("home"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists. Please log in.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as db:
            user = db.execute(
                "SELECT id, name, email, password_hash FROM users WHERE email = ?",
                (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("home"))

        flash("Email or password is incorrect.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()
    if not user_message:
        return jsonify({"reply": "Please enter a message."}), 400

    reply = get_response(user_message)

    with get_db() as db:
        db.execute(
            "INSERT INTO chat_history (user_id, sender, text) VALUES (?, 'user', ?)",
            (session["user_id"], user_message[:2000])
        )
        db.execute(
            "INSERT INTO chat_history (user_id, sender, text) VALUES (?, 'bot', ?)",
            (session["user_id"], reply)
        )
        kind, condition_name = read_outcome(reply)
        db.execute(
            "INSERT INTO activity (user_id, kind, condition_name) VALUES (?, ?, ?)",
            (session["user_id"], kind, condition_name)
        )
    return jsonify({"reply": reply})


@app.route("/history", methods=["GET"])
@login_required
def history():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT sender, text FROM (
                SELECT id, sender, text FROM chat_history
                WHERE user_id = ? ORDER BY id DESC LIMIT 100
            ) ORDER BY id ASC
            """,
            (session["user_id"],)
        ).fetchall()
    return jsonify({"messages": [{"sender": r["sender"], "text": r["text"]} for r in rows]})


@app.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    with get_db() as db:
        db.execute("DELETE FROM chat_history WHERE user_id = ?", (session["user_id"],))
    return jsonify({"ok": True})


@app.route("/feedback", methods=["POST"])
@login_required
def feedback():
    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    user_message = str(data.get("user_message", "")).strip()[:1000]
    bot_reply = str(data.get("bot_reply", "")).strip()[:3000]

    if rating not in ("like", "dislike") or not user_message or not bot_reply:
        return jsonify({"error": "Invalid feedback."}), 400

    with get_db() as db:
        db.execute(
            "INSERT INTO feedback (user_id, user_message, bot_reply, rating) VALUES (?, ?, ?, ?)",
            (session["user_id"], user_message, bot_reply, rating)
        )
    return jsonify({"ok": True})


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM activity WHERE user_id = ?", (user_id,)).fetchone()[0]
        emergencies = db.execute(
            "SELECT COUNT(*) FROM activity WHERE user_id = ? AND kind = 'emergency'", (user_id,)
        ).fetchone()[0]
        likes = db.execute(
            "SELECT COUNT(*) FROM feedback WHERE user_id = ? AND rating = 'like'", (user_id,)
        ).fetchone()[0]
        dislikes = db.execute(
            "SELECT COUNT(*) FROM feedback WHERE user_id = ? AND rating = 'dislike'", (user_id,)
        ).fetchone()[0]
        top_rows = db.execute(
            """
            SELECT condition_name, COUNT(*) AS times FROM activity
            WHERE user_id = ? AND kind = 'match'
            GROUP BY condition_name ORDER BY times DESC, condition_name LIMIT 5
            """,
            (user_id,)
        ).fetchall()
        recent = db.execute(
            """
            SELECT kind, condition_name, strftime('%Y-%m-%dT%H:%M:%SZ', created_at) AS when_utc
            FROM activity WHERE user_id = ? ORDER BY id DESC LIMIT 5
            """,
            (user_id,)
        ).fetchall()

    rated = likes + dislikes
    helpful_rate = round(likes * 100 / rated) if rated else None
    biggest = top_rows[0]["times"] if top_rows else 1
    top_conditions = [
        {"name": row["condition_name"], "times": row["times"], "percent": round(row["times"] * 100 / biggest)}
        for row in top_rows
    ]
    return render_template(
        "dashboard.html",
        total=total, emergencies=emergencies, likes=likes, dislikes=dislikes,
        rated=rated, helpful_rate=helpful_rate,
        top_conditions=top_conditions, recent=recent
    )


@app.route("/emergency")
@login_required
def emergency():
    return render_template("emergency.html")


@app.route("/about")
@login_required
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)