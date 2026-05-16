import os
import time
import hashlib
import random
import json
import urllib.request
import urllib.error
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    init_db, get_categories, get_downloads, get_download_by_id,
    add_download, update_download, delete_download,
    increment_download_count, get_news, add_news, delete_news,
    get_setting, update_setting, get_stats,
    add_category, delete_category, get_category_by_id, get_db,
    update_category,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADMIN_USER = "admin"
ADMIN_PASS_HASH = generate_password_hash("admin")

app = Flask(__name__)
app.secret_key = "svpx_s3cr3t_k3y_2026"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["ALLOWED_EXTENSIONS"] = {"zip", "rar", "7z", "exe", "dll", "asi", "cs", "lua", "png", "jpg", "jpeg", "gif", "txt", "pdf", "cfg", "ini", "mp3", "wav", "torrent", "txd", "dff", "col", "img"}

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

with app.app_context():
    init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please login first.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

def format_file_size(size):
    if size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"

@app.context_processor
def inject_globals():
    return {
        "categories": get_categories(),
        "site_name": get_setting("site_name"),
        "server_name": get_setting("server_name"),
        "server_ip": get_setting("server_ip"),
        "discord_link": get_setting("discord_link"),
        "website_version": get_setting("website_version"),
        "current_year": datetime.now().year,
        "format_file_size": format_file_size,
        "get_setting": get_setting,
    }

@app.route("/")
def index():
    latest_news = get_news(limit=3)
    latest_downloads = get_downloads()[:8]
    stats = get_stats()
    return render_template("index.html", news=latest_news, latest_downloads=latest_downloads, stats=stats)

@app.route("/downloads")
def downloads():
    category = request.args.get("category")
    search = request.args.get("search", "").strip()
    all_downloads = get_downloads(category_slug=category, search=search if search else None)
    return render_template("downloads.html", downloads=all_downloads, active_category=category, search_query=search)

@app.route("/download/<int:download_id>")
def download_file(download_id):
    item = get_download_by_id(download_id)
    if not item:
        abort(404)
    if item["filename"]:
        increment_download_count(download_id)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], item["filename"])
        if os.path.exists(file_path):
            return send_from_directory(
                app.config["UPLOAD_FOLDER"],
                item["filename"],
                as_attachment=True,
                download_name=item["original_filename"]
            )
    return redirect(item["file_url"] or url_for("downloads"))

@app.route("/news")
def news_page():
    all_news = get_news()
    return render_template("news.html", news=all_news)

@app.route("/discord/status")
def discord_status():
    invite_code = "zp4qXWwWw"
    url = f"https://discord.com/api/v10/invites/{invite_code}?with_counts=true&with_expiration=true"
    req = urllib.request.Request(url, headers={"User-Agent": "SVPX-Community/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return jsonify({"error": "Unable to fetch Discord data"}), 502
    guild = data.get("guild", {})
    icon_url = ""
    if guild.get("id") and guild.get("icon"):
        ext = "gif" if guild["icon"].startswith("a_") else "png"
        icon_url = f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.{ext}?size=256"
    return jsonify({
        "name": guild.get("name", "SVPX Community"),
        "icon": icon_url,
        "description": guild.get("description", ""),
        "members": data.get("approximate_member_count", 0),
        "online": data.get("approximate_presence_count", 0),
        "invite": f"https://discord.gg/{invite_code}",
    })

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Welcome back.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials.", "error")
        return redirect(url_for("admin_login"))
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.", "info")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = get_stats()
    cats = get_categories()
    return render_template("admin/dashboard.html", stats=stats, categories=cats)

@app.route("/admin/downloads")
@admin_required
def admin_downloads():
    all_downloads = get_downloads()
    cats = get_categories()
    return render_template("admin/downloads.html", downloads=all_downloads, categories=cats)

@app.route("/admin/downloads/add", methods=["POST"])
@admin_required
def admin_add_download():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category_id = request.form.get("category_id", "").strip()
    version = request.form.get("version", "1.0").strip()
    image_url = request.form.get("image_url", "").strip()
    file_url = request.form.get("file_url", "").strip()

    if not title or not category_id or not category_id.isdigit():
        flash("Title and category are required.", "error")
        return redirect(url_for("admin_downloads"))

    filename = None
    original_filename = None
    file_size = 0

    if "file" in request.files:
        f = request.files["file"]
        if f and f.filename:
            if not allowed_file(f.filename):
                flash("File type not allowed.", "error")
                return redirect(url_for("admin_downloads"))
            original_filename = f.filename
            ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""
            safe_name = f"{int(time.time())}_{hashlib.md5(original_filename.encode()).hexdigest()[:8]}.{ext}"
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))
            filename = safe_name
            file_size = os.path.getsize(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))

    add_download(title, description, int(category_id), filename, original_filename, file_size, image_url, file_url, version)
    flash(f"'{title}' published.", "success")
    return redirect(url_for("admin_downloads"))

@app.route("/admin/downloads/edit/<int:download_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_download(download_id):
    item = get_download_by_id(download_id)
    if not item:
        abort(404)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", "").strip()
        version = request.form.get("version", "1.0").strip()
        image_url = request.form.get("image_url", "").strip()
        file_url = request.form.get("file_url", "").strip()

        if not title or not category_id:
            flash("Title and category required.", "error")
            return redirect(url_for("admin_edit_download", download_id=download_id))

        filename = item["filename"]
        original_filename = item["original_filename"]
        file_size = item["file_size"]

        if "file" in request.files:
            f = request.files["file"]
            if f and f.filename:
                if not allowed_file(f.filename):
                    flash("File type not allowed.", "error")
                    return redirect(url_for("admin_edit_download", download_id=download_id))
                if item["filename"]:
                    old = os.path.join(app.config["UPLOAD_FOLDER"], item["filename"])
                    if os.path.exists(old):
                        os.remove(old)
                original_filename = f.filename
                ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""
                safe_name = f"{int(time.time())}_{hashlib.md5(original_filename.encode()).hexdigest()[:8]}.{ext}"
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))
                filename = safe_name
                file_size = os.path.getsize(os.path.join(app.config["UPLOAD_FOLDER"], safe_name))

        update_download(download_id, title, description, int(category_id), version, image_url, file_url, filename, original_filename, file_size)
        flash("Updated.", "success")
        return redirect(url_for("admin_downloads"))

    cats = get_categories()
    return render_template("admin/edit_download.html", item=item, categories=cats)

@app.route("/admin/downloads/delete/<int:download_id>")
@admin_required
def admin_delete_download(download_id):
    item = get_download_by_id(download_id)
    if item and item["filename"]:
        fp = os.path.join(app.config["UPLOAD_FOLDER"], item["filename"])
        if os.path.exists(fp):
            os.remove(fp)
    delete_download(download_id)
    flash("Deleted.", "success")
    return redirect(url_for("admin_downloads"))

@app.route("/admin/news")
@admin_required
def admin_news():
    all_news = get_news()
    return render_template("admin/news.html", news=all_news)

@app.route("/admin/news/add", methods=["POST"])
@admin_required
def admin_add_news():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    if not title or not content:
        flash("Title and content required.", "error")
    else:
        add_news(title, content, session.get("admin_username", "SVPX Admin"))
        flash("News published.", "success")
    return redirect(url_for("admin_news"))

@app.route("/admin/news/delete/<int:news_id>")
@admin_required
def admin_delete_news(news_id):
    delete_news(news_id)
    flash("Deleted.", "success")
    return redirect(url_for("admin_news"))

@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip()
        icon = request.form.get("icon", "fas fa-folder").strip()
        import re
        slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))
        if name and slug:
            if add_category(name, slug, icon):
                flash(f"Category '{name}' created.", "success")
            else:
                flash("Category exists.", "error")
        else:
            flash("Name and slug required.", "error")
        return redirect(url_for("admin_categories"))
    return render_template("admin/categories.html", categories=get_categories())

@app.route("/admin/categories/delete/<int:category_id>")
@admin_required
def admin_delete_category(category_id):
    delete_category(category_id)
    flash("Deleted.", "success")
    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_category(category_id):
    cat = get_category_by_id(category_id)
    if not cat:
        abort(404)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip()
        icon = request.form.get("icon", "fas fa-folder").strip()
        import re
        slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))
        if name and slug:
            update_category(category_id, name, slug, icon)
            flash(f"Category '{name}' updated.", "success")
        else:
            flash("Name and slug required.", "error")
        return redirect(url_for("admin_categories"))
    return render_template("admin/edit_category.html", cat=cat)

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    if request.method == "POST":
        update_setting("site_name", request.form.get("site_name", "SVPX Community"))
        update_setting("server_name", request.form.get("server_name", ""))
        update_setting("server_ip", request.form.get("server_ip", ""))
        update_setting("max_players", request.form.get("max_players", "500"))
        update_setting("discord_link", request.form.get("discord_link", ""))
        update_setting("description", request.form.get("description", ""))
        flash("Settings saved.", "success")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
