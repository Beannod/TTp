
import os
import sqlite3
import sys
import subprocess
import socket
import threading
import uuid
import ipaddress
import webbrowser
import io
import base64
import datetime

# ...existing code...

from flask import Flask, request, session, redirect, render_template_string, jsonify, send_from_directory

# --- DB integration ---
from db import init_db, insert_upload

# ...existing code...

PORT = 5000
app = Flask(__name__)
app.secret_key = "secure-session"
init_db()

# Serve uploaded files for gallery (must be after app is defined)
@app.route('/uploads/<folder>/<filename>')
def uploaded_file(folder, filename):
    folder_path = os.path.join(UPLOAD_PATH, folder)
    return send_from_directory(folder_path, filename)
import os
import sqlite3
import sys
import subprocess
import socket
import threading
import uuid
import ipaddress
import webbrowser
import io
import base64
import datetime

print("===================")
print("Current time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("(Press Enter to use default values shown in brackets)")
print("===================\n")

from flask import Flask, request, session, redirect, render_template_string, jsonify

# --- DB integration ---
from db import init_db, insert_upload




import qrcode


PASSWORD = input("Set admin password [binod]: ").strip() or "binod"
SECRET_TOKEN = input("QR token (Enter = auto): ").strip() or uuid.uuid4().hex[:10]

DEFAULT_PATH = r"D:\Software\TTp"
DEFAULT_FOLDER = "uploads"
UPLOAD_PATH = input(f"Set upload base path [{DEFAULT_PATH}]: ").strip() or DEFAULT_PATH
UPLOAD_FOLDER = input(f"Set upload folder name [{DEFAULT_FOLDER}]: ").strip() or DEFAULT_FOLDER
CURRENT_FOLDER = os.path.join(UPLOAD_PATH, UPLOAD_FOLDER)
os.makedirs(CURRENT_FOLDER, exist_ok=True)
ADMIN_FOLDER = UPLOAD_FOLDER

# Initialize DB
PORT = 5000
app = Flask(__name__)
app.secret_key = "secure-session"
init_db()
# ---------------- CREATE FOLDER ENDPOINT ----------------
@app.post("/create-folder")
def create_folder():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    data = request.get_json()
    folder = data.get("folder", "").strip()
    import json
    if not folder or any(c in folder for c in "/\\:><|?*"):
        return jsonify({"status": "error", "error": "Invalid folder name"})
    safe_folder = os.path.basename(folder)
    folder_path = os.path.join(UPLOAD_PATH, safe_folder)
    try:
        os.makedirs(folder_path, exist_ok=True)
        global CURRENT_FOLDER, ADMIN_FOLDER
        CURRENT_FOLDER = folder_path
        ADMIN_FOLDER = safe_folder
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})
import os
import sys
import subprocess
import socket
import threading
import uuid
import ipaddress
import webbrowser
import io
import base64

from flask import Flask, request, session, redirect, render_template_string



def get_ip():
    return socket.gethostbyname(socket.gethostname())

def get_client_ip():
    return request.remote_addr

def same_network(ip):
    try:
        net = ipaddress.ip_network(get_ip() + "/24", strict=False)
        return ipaddress.ip_address(ip) in net
    except:
        return False

def safe_filename(name):
    return os.path.basename(name).replace("/", "_")

def is_logged_in():
    return session.get("logged_in")

def security_ok():
    return same_network(get_client_ip()) and is_logged_in()

def generate_qr(url):
    import qrcode
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/login", methods=["GET", "POST"])
def login():
    token = request.args.get("token")
    if request.method == "GET":
        if token != SECRET_TOKEN:
            return "❌ Invalid QR", 403
        session["qr_ok"] = True
        # Serve modern login page
        with open("login.html", "r", encoding="utf-8") as f:
            return f.read()
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        return "Wrong password"


# ---------------- HOME ----------------
@app.get("/")
def home():
    if not security_ok():
        return redirect(f"/login?token={SECRET_TOKEN}")
    ip = get_ip()
    url = f"http://{ip}:{PORT}/login?token={SECRET_TOKEN}"
    qr = generate_qr(url)
    with open("upload.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{qr}}", qr).replace("{{folder}}", ADMIN_FOLDER)
    return html


# ---------------- UPLOAD ----------------
@app.post("/")
def upload():
    if not security_ok():
        return "Unauthorized", 401
    files = request.files.getlist("file")
    if not files or not any(f.filename for f in files):
        return "No file"

    import json
    log_path = os.path.join(UPLOAD_PATH, "uploads_log.json")
    upload_log = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                upload_log = data.get("uploads", [])
        except Exception:
            upload_log = []

    # EXIF extraction for images only
    def extract_exif_info(path):
        try:
            from PIL import Image
            import piexif
            img = Image.open(path)
            exif_data = img.info.get('exif')
            if not exif_data:
                return {}
            exif_dict = piexif.load(exif_data)
            def get_tag(dct, key):
                val = dct.get(key)
                if isinstance(val, bytes):
                    return val.decode(errors='ignore')
                return val
            # Basic fields
            date = get_tag(exif_dict['Exif'], piexif.ExifIFD.DateTimeOriginal)
            make = get_tag(exif_dict['0th'], piexif.ImageIFD.Make)
            model = get_tag(exif_dict['0th'], piexif.ImageIFD.Model)
            orientation = get_tag(exif_dict['0th'], piexif.ImageIFD.Orientation)
            exposure = get_tag(exif_dict['Exif'], piexif.ExifIFD.ExposureTime)
            iso = get_tag(exif_dict['Exif'], piexif.ExifIFD.ISOSpeedRatings)
            focal_length = get_tag(exif_dict['Exif'], piexif.ExifIFD.FocalLength)
            software = get_tag(exif_dict['0th'], piexif.ImageIFD.Software)
            lens_model = get_tag(exif_dict['Exif'], piexif.ExifIFD.LensModel)
            aperture = get_tag(exif_dict['Exif'], piexif.ExifIFD.FNumber)
            flash = get_tag(exif_dict['Exif'], piexif.ExifIFD.Flash)
            white_balance = get_tag(exif_dict['Exif'], piexif.ExifIFD.WhiteBalance)
            metering_mode = get_tag(exif_dict['Exif'], piexif.ExifIFD.MeteringMode)
            # GPS
            gps = exif_dict.get('GPS', {})
            lat = lon = None
            if gps:
                def conv(coord, ref):
                    d, m, s = coord
                    val = d[0]/d[1] + m[0]/m[1]/60 + s[0]/s[1]/3600
                    if ref in [b'S', b'W', 'S', 'W']:
                        val = -val
                    return val
                if piexif.GPSIFD.GPSLatitude in gps and piexif.GPSIFD.GPSLatitudeRef in gps:
                    lat = conv(gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef])
                if piexif.GPSIFD.GPSLongitude in gps and piexif.GPSIFD.GPSLongitudeRef in gps:
                    lon = conv(gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef])
            # Resolution
            resolution = None
            try:
                resolution = f"{img.width}x{img.height}"
            except Exception:
                pass
            return {
                "date": date,
                "lat": lat,
                "lon": lon,
                "make": make,
                "model": model,
                "orientation": orientation,
                "exposure": exposure,
                "iso": iso,
                "focal_length": focal_length,
                "software": software,
                "lens_model": lens_model,
                "aperture": aperture,
                "flash": flash,
                "white_balance": white_balance,
                "metering_mode": metering_mode,
                "resolution": resolution
            }
        except Exception:
            return {}

    last_upload_time = None

    for file in files:
        if file and file.filename:
            filename = str(uuid.uuid4()) + "_" + safe_filename(file.filename)
            os.makedirs(CURRENT_FOLDER, exist_ok=True)
            file_path = os.path.join(CURRENT_FOLDER, filename)
            file.save(file_path)
            meta = {}
            # Only extract EXIF for images
            if file.filename.lower().endswith((".jpg", ".jpeg", ".tiff", ".heic")):
                meta = extract_exif_info(file_path)
            upload_time = datetime.datetime.now().isoformat()
            last_upload_time = upload_time
            upload_log.append({
                "filename": filename,
                "original": file.filename,
                "size": file.content_length or 0,
                "upload_time": upload_time,
                "exif": meta,
                "folder": os.path.relpath(CURRENT_FOLDER, UPLOAD_PATH)
            })
            # --- Log to SQLite DB ---
            insert_upload(
                filename=filename,
                original=file.filename,
                size=file.content_length or 0,
                upload_time=upload_time,
                exif=meta,
                folder=os.path.relpath(CURRENT_FOLDER, UPLOAD_PATH)
            )

    # Store/update a summary with last updated date
    summary = {
        "updated": last_upload_time,
        "total_uploads": len(upload_log),
        "uploads": upload_log
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return "OK"

# ---------------- LIST UPLOADS ENDPOINT ----------------
@app.get("/list-uploads")
def list_uploads():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    folder = request.args.get("folder", "").strip()
    if not folder or any(c in folder for c in "/\\:><|?*"):
        return jsonify({"status": "error", "error": "Invalid folder name"})
    folder_path = os.path.join(UPLOAD_PATH, folder)
    if not os.path.exists(folder_path):
        return jsonify({"status": "ok", "files": []})
    try:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return jsonify({"status": "ok", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})
# ---------------- START ----------------
if __name__ == "__main__":
    ip = get_ip()
    url = f"http://{ip}:{PORT}/login?token={SECRET_TOKEN}"

    print("\n========================")
    print("📤 SERVER READY")
    print("PC:   http://127.0.0.1:5000")
    print("PHONE:", url)
    print("========================\n")

    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host="0.0.0.0", port=PORT)