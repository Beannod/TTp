


from flask import Flask, jsonify, redirect, request, send_from_directory, session
import base64
import datetime
import io
import ipaddress
import os
import random
import socket
import subprocess
import threading
import uuid
import webbrowser
from db import get_db_path, init_db, insert_upload

APP_VERSION = "2"
PORT = 5000


print("===================")
print("Current time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("(Press Enter to use default values shown in brackets)")
print("===================\n")



# --- Ephemeral SECRET_TOKEN logic (expires on server stop) ---
user_token = input("QR token (Enter = auto): ").strip()
SECRET_TOKEN = user_token or uuid.uuid4().hex[:10]

PASSWORD = input("Set admin password [binod]: ").strip() or "binod"

DEFAULT_PATH = r"D:\Software\TTp"
DEFAULT_FOLDER = "uploads"
UPLOAD_PATH = input(f"Set upload base path [{DEFAULT_PATH}]: ").strip() or DEFAULT_PATH
UPLOAD_FOLDER = input(f"Set upload folder name [{DEFAULT_FOLDER}]: ").strip() or DEFAULT_FOLDER

CURRENT_FOLDER = os.path.join(UPLOAD_PATH, UPLOAD_FOLDER)
os.makedirs(CURRENT_FOLDER, exist_ok=True)
ADMIN_FOLDER = UPLOAD_FOLDER



# Flask app must be initialized before any route decorators
app = Flask(__name__)
app.secret_key = "secure-session"
init_db(UPLOAD_PATH)


def generate_wifi_qr(ssid, password, auth):
    # WiFi QR format: WIFI:T:WPA;S:mynetwork;P:mypass;H:false;;
    import qrcode
    qr_str = f"WIFI:T:{auth};S:{ssid};P:{password};;"
    img = qrcode.make(qr_str)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()





# Simple test endpoint to verify server instance
@app.get("/test-alive")
def test_alive():
    return "Server is running", 200


app = Flask(__name__)
app.secret_key = "secure-session"
init_db(UPLOAD_PATH)


def get_ip():
    # Best-effort LAN IP detection. On Windows, gethostbyname(hostname) often returns 127.0.0.1.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # No packets are actually sent for UDP connect; it just picks a route/interface.
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
        finally:
            s.close()
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip
    except Exception:
        return "127.0.0.1"


def get_client_ip():
    return request.remote_addr


def same_network(ip):
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_loopback:
            return True
        # Allow private LAN addresses (typical home/office WiFi). Still blocks public IPs.
        if addr.is_private:
            return True
        net = ipaddress.ip_network(get_ip() + "/24", strict=False)
        return addr in net
    except Exception:
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



# Start/stop Windows WiFi hotspot and return SSID/password
@app.post("/start-hotspot")
def start_hotspot():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    ssid = f"Uploader_{random.randint(1000,9999)}"
    password = uuid.uuid4().hex[:12]
    try:
        subprocess.run(["netsh", "wlan", "set", "hostednetwork", f"mode=allow", f"ssid={ssid}", f"key={password}"], capture_output=True, text=True, timeout=10)
        result = subprocess.run(["netsh", "wlan", "start", "hostednetwork"], capture_output=True, text=True, timeout=10)
        if "started" in result.stdout.lower():
            return jsonify({"status": "ok", "ssid": ssid, "password": password, "auth": "WPA2"})
        else:
            return jsonify({"status": "error", "error": result.stdout + result.stderr})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Serve uploaded files for gallery
@app.route("/uploads/<folder>/<filename>")
def uploaded_file(folder, filename):
    folder_path = os.path.join(UPLOAD_PATH, folder)
    return send_from_directory(folder_path, filename)


@app.post("/update-app")
def update_app():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    try:
        # Auto-commit any local changes before pulling
        subprocess.run(["git", "add", "."], cwd=os.path.dirname(__file__), capture_output=True, text=True, timeout=10)
        commit_result = subprocess.run([
            "git", "commit", "-m", "Auto-commit before update"
        ], cwd=os.path.dirname(__file__), capture_output=True, text=True, timeout=10)
        # Ignore 'nothing to commit' error
        pull_result = subprocess.run(
            ["git", "pull"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if pull_result.returncode == 0:
            return jsonify({"status": "ok", "output": pull_result.stdout.strip()})
        return jsonify({"status": "error", "error": pull_result.stderr.strip()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.post("/create-folder")
def create_folder():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    folder = (data.get("folder") or "").strip()
    if not folder or any(c in folder for c in "/\\:><|?*"):
        return jsonify({"status": "error", "error": "Invalid folder name"})
    safe_folder = os.path.basename(folder)
    folder_path = os.path.join(UPLOAD_PATH, safe_folder)
    try:
        os.makedirs(folder_path, exist_ok=True)
        global CURRENT_FOLDER, ADMIN_FOLDER
        CURRENT_FOLDER = folder_path
        ADMIN_FOLDER = safe_folder
        return jsonify({"status": "ok", "folder": safe_folder})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.get("/folders")
def list_folders():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    try:
        folders = []
        for name in os.listdir(UPLOAD_PATH):
            full = os.path.join(UPLOAD_PATH, name)
            if os.path.isdir(full) and not name.startswith(".") and name != "__pycache__":
                folders.append(name)
        folders.sort(key=lambda s: s.lower())
        return jsonify({"status": "ok", "folders": folders, "current": ADMIN_FOLDER})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.get("/stats")
def stats():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    try:
        import shutil

        total = used = free = None
        try:
            du = shutil.disk_usage(UPLOAD_PATH)
            total, used, free = du.total, du.used, du.free
        except Exception:
            pass

        folder = request.args.get("folder", "").strip() or ADMIN_FOLDER
        if any(c in folder for c in "/\\:><|?*"):
            return jsonify({"status": "error", "error": "Invalid folder name"})
        folder_path = os.path.join(UPLOAD_PATH, folder)
        file_count = 0
        bytes_count = 0
        if os.path.exists(folder_path):
            for name in os.listdir(folder_path):
                fp = os.path.join(folder_path, name)
                if os.path.isfile(fp):
                    file_count += 1
                    try:
                        bytes_count += os.path.getsize(fp)
                    except Exception:
                        pass
        return jsonify(
            {
                "status": "ok",
                "folder": folder,
                "file_count": file_count,
                "folder_bytes": bytes_count,
                "disk_total": total,
                "disk_used": used,
                "disk_free": free,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.get("/folder-items")
def folder_items():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    try:
        folders_q = (request.args.get("folders") or "").strip()
        if not folders_q:
            return jsonify({"status": "error", "error": "Missing folders"})
        folders = [f.strip() for f in folders_q.split(",") if f.strip()]
        if not folders:
            return jsonify({"status": "error", "error": "Missing folders"})

        def is_safe_folder(name):
            if any(c in name for c in "/\\:><|?*"):
                return False
            # Prevent traversal (..)
            if name in (".", ".."):
                return False
            return os.path.basename(name) == name

        results = {}
        for folder in folders[:20]:
            if not is_safe_folder(folder):
                return jsonify({"status": "error", "error": f"Invalid folder name: {folder}"})
            folder_path = os.path.join(UPLOAD_PATH, folder)
            items = []
            if os.path.exists(folder_path):
                for name in os.listdir(folder_path):
                    fp = os.path.join(folder_path, name)
                    is_dir = os.path.isdir(fp)
                    size = None
                    mtime = None
                    if not is_dir and os.path.isfile(fp):
                        try:
                            size = os.path.getsize(fp)
                        except Exception:
                            size = None
                    try:
                        mtime = os.path.getmtime(fp)
                    except Exception:
                        mtime = None
                    items.append(
                        {
                            "name": name,
                            "is_dir": bool(is_dir),
                            "size": size,
                            "mtime": mtime,
                        }
                    )
            items.sort(key=lambda it: (0 if it["is_dir"] else 1, (it["name"] or "").lower()))
            results[folder] = items
        return jsonify({"status": "ok", "folders": results})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


def _safe_folder_and_file(folder, filename):
    if not folder or any(c in folder for c in "/\\:><|?*") or folder in (".", ".."):
        return None, None
    if os.path.basename(folder) != folder:
        return None, None
    if not filename or any(c in filename for c in "/\\:><|?*"):
        return None, None
    safe_file = os.path.basename(filename)
    folder_path = os.path.join(UPLOAD_PATH, folder)
    file_path = os.path.join(folder_path, safe_file)
    return safe_file, file_path


@app.get("/pdf-info")
def pdf_info():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    folder = (request.args.get("folder") or "").strip()
    filename = (request.args.get("file") or "").strip()
    safe_file, file_path = _safe_folder_and_file(folder, filename)
    if not safe_file or not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "error": "Not found"}), 404
    if not safe_file.lower().endswith(".pdf"):
        return jsonify({"status": "error", "error": "Not a PDF"}), 400
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        n = doc.page_count
        doc.close()
        return jsonify({"status": "ok", "pages": n})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.get("/pdf-page")
def pdf_page():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    folder = (request.args.get("folder") or "").strip()
    filename = (request.args.get("file") or "").strip()
    page_s = (request.args.get("page") or "0").strip()
    zoom_s = (request.args.get("zoom") or "1.5").strip()
    safe_file, file_path = _safe_folder_and_file(folder, filename)
    if not safe_file or not file_path or not os.path.exists(file_path):
        return "Not found", 404
    if not safe_file.lower().endswith(".pdf"):
        return "Not a PDF", 400
    try:
        page_n = int(page_s)
    except Exception:
        page_n = 0
    try:
        zoom = float(zoom_s)
        if zoom < 0.5:
            zoom = 0.5
        if zoom > 3.0:
            zoom = 3.0
    except Exception:
        zoom = 1.5
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        if page_n < 0 or page_n >= doc.page_count:
            doc.close()
            return "Page out of range", 400
        page = doc.load_page(page_n)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        data = pix.tobytes("png")
        doc.close()
        return data, 200, {"Content-Type": "image/png"}
    except Exception as e:
        return f"Render error: {e}", 500


@app.post("/pdf-apply-highlights")
def pdf_apply_highlights():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    folder = (data.get("folder") or "").strip()
    filename = (data.get("file") or "").strip()
    highlights = data.get("highlights") or []
    safe_file, file_path = _safe_folder_and_file(folder, filename)
    if not safe_file or not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "error": "Not found"}), 404
    if not safe_file.lower().endswith(".pdf"):
        return jsonify({"status": "error", "error": "Not a PDF"}), 400
    if not isinstance(highlights, list) or not highlights:
        return jsonify({"status": "error", "error": "No highlights"}), 400
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        applied = 0
        for h in highlights[:500]:
            try:
                page_n = int(h.get("page", 0))
                x0 = float(h.get("x0"))
                y0 = float(h.get("y0"))
                x1 = float(h.get("x1"))
                y1 = float(h.get("y1"))
            except Exception:
                continue
            if page_n < 0 or page_n >= doc.page_count:
                continue
            # normalized coordinates [0..1] in page space
            x0, x1 = sorted([max(0.0, min(1.0, x0)), max(0.0, min(1.0, x1))])
            y0, y1 = sorted([max(0.0, min(1.0, y0)), max(0.0, min(1.0, y1))])
            if (x1 - x0) < 0.002 or (y1 - y0) < 0.002:
                continue
            page = doc.load_page(page_n)
            r = page.rect
            rect = fitz.Rect(x0 * r.width, y0 * r.height, x1 * r.width, y1 * r.height)
            annot = page.add_highlight_annot(rect)
            if annot:
                annot.set_colors(stroke=(1, 1, 0))  # yellow
                annot.update()
                applied += 1
        if applied:
            doc.saveIncr()
        doc.close()
        return jsonify({"status": "ok", "applied": applied})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    token = request.args.get("token")
    if request.method == "GET":
        if token != SECRET_TOKEN:
            return "Invalid QR", 403
        session["qr_ok"] = True
        with open("login.html", "r", encoding="utf-8") as f:
            return f.read()
    if request.form.get("password") == PASSWORD:
        session["logged_in"] = True
        return redirect("/")
    return "Wrong password", 403


@app.get("/")
def home():
    if not security_ok():
        return redirect(f"/login?token={SECRET_TOKEN}")
    ip = get_ip()
    url = f"http://{ip}:{PORT}/login?token={SECRET_TOKEN}"
    qr = generate_qr(url)

    # Get WiFi info (Windows only)
    wifi_ssid = wifi_pass = wifi_auth = None
    try:
        import subprocess
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=3)
        lines = result.stdout.splitlines()
        for line in lines:
            if "SSID" in line and ":" in line and not wifi_ssid:
                wifi_ssid = line.split(":",1)[1].strip().strip('"')
        # Find all authentications, prefer WPA3 > WPA2 > WPA
        auths = [line.split(":",1)[1].strip().upper() for line in lines if "Authentication" in line and ":" in line]
        wifi_auth = None
        for preferred in ["WPA3-PERSONAL", "WPA2-PERSONAL", "WPA-PERSONAL"]:
            for a in auths:
                if preferred in a:
                    wifi_auth = preferred.replace("-PERSONAL", "")
                    break
            if wifi_auth:
                break
        if not wifi_auth and auths:
            wifi_auth = auths[0].split("-")[0]  # fallback to first
        if wifi_ssid:
            result2 = subprocess.run(["netsh", "wlan", "show", "profile", f"name={wifi_ssid}", "key=clear"], capture_output=True, text=True, timeout=3)
            for line in result2.stdout.splitlines():
                if "Key Content" in line:
                    wifi_pass = line.split(":",1)[1].strip()
                    break
    except Exception:
        pass
    wifi_qr = ""
    if wifi_ssid and wifi_pass and wifi_auth:
        wifi_qr = generate_wifi_qr(wifi_ssid, wifi_pass, wifi_auth)

    with open("upload.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{qr}}", qr).replace("{{folder}}", ADMIN_FOLDER).replace("{{version}}", APP_VERSION)
    html = html.replace("{{wifi_qr}}", wifi_qr).replace("{{wifi_ssid}}", wifi_ssid or "").replace("{{wifi_pass}}", wifi_pass or "").replace("{{wifi_auth}}", wifi_auth or "")
    return html


@app.get("/gallery")
def gallery():
    if not security_ok():
        return redirect(f"/login?token={SECRET_TOKEN}")
    with open("gallery.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{folder}}", ADMIN_FOLDER).replace("{{version}}", APP_VERSION)
    return html


@app.post("/")
def upload():
    if not security_ok():
        return "Unauthorized", 401

    global CURRENT_FOLDER, ADMIN_FOLDER

    try:
        files = request.files.getlist("file")
        if not files or not any(f.filename for f in files):
            return "No file", 400

        # Optional folder override from client (still locked to UPLOAD_PATH root).
        folder_override = (request.form.get("folder") or "").strip()
        target_folder = ADMIN_FOLDER
        if folder_override:
            if any(c in folder_override for c in "/\\:><|?*") or folder_override in (".", ".."):
                return "Invalid folder", 400
            target_folder = os.path.basename(folder_override)

        ADMIN_FOLDER = target_folder
        CURRENT_FOLDER = os.path.join(UPLOAD_PATH, target_folder)
        os.makedirs(CURRENT_FOLDER, exist_ok=True)

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

        def extract_exif_info(path):
            # Best-effort EXIF extraction (capture time + GPS + camera info) for JPEG/TIFF/HEIC.
            # Returns keys compatible with db.py insert_upload mapping.
            try:
                from PIL import ExifTags, Image

                img = Image.open(path)
                exif = img.getexif()
                if not exif:
                    return {}

                tags = {ExifTags.TAGS.get(k, k): exif.get(k) for k in exif.keys()}

                date = tags.get("DateTimeOriginal") or tags.get("DateTime")
                make = tags.get("Make")
                model = tags.get("Model")
                orientation = tags.get("Orientation")
                exposure = tags.get("ExposureTime")
                iso = tags.get("ISOSpeedRatings")
                focal_length = tags.get("FocalLength")
                software = tags.get("Software")
                lens_model = tags.get("LensModel")
                aperture = tags.get("FNumber")
                flash = tags.get("Flash")
                white_balance = tags.get("WhiteBalance")
                metering_mode = tags.get("MeteringMode")

                def _ratio_to_float(x):
                    try:
                        return float(x[0]) / float(x[1])
                    except Exception:
                        try:
                            return float(x)
                        except Exception:
                            return None

                def _dms_to_deg(dms, ref):
                    d = _ratio_to_float(dms[0])
                    m = _ratio_to_float(dms[1])
                    s = _ratio_to_float(dms[2])
                    if d is None or m is None or s is None:
                        return None
                    val = d + (m / 60.0) + (s / 3600.0)
                    if ref in ("S", "W", b"S", b"W"):
                        val = -val
                    return val

                lat = lon = None
                gps = tags.get("GPSInfo")
                if isinstance(gps, dict) and gps:
                    gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}
                    if "GPSLatitude" in gps_tags and "GPSLatitudeRef" in gps_tags:
                        lat = _dms_to_deg(gps_tags["GPSLatitude"], gps_tags["GPSLatitudeRef"])
                    if "GPSLongitude" in gps_tags and "GPSLongitudeRef" in gps_tags:
                        lon = _dms_to_deg(gps_tags["GPSLongitude"], gps_tags["GPSLongitudeRef"])

                resolution = None
                try:
                    resolution = f"{img.width}x{img.height}"
                except Exception:
                    pass

                return {
                    "date": str(date) if date else None,
                    "lat": lat,
                    "lon": lon,
                    "make": str(make) if make is not None else None,
                    "model": str(model) if model is not None else None,
                    "orientation": str(orientation) if orientation is not None else None,
                    "exposure": str(exposure) if exposure is not None else None,
                    "iso": str(iso) if iso is not None else None,
                    "focal_length": str(focal_length) if focal_length is not None else None,
                    "software": str(software) if software is not None else None,
                    "lens_model": str(lens_model) if lens_model is not None else None,
                    "aperture": str(aperture) if aperture is not None else None,
                    "flash": str(flash) if flash is not None else None,
                    "white_balance": str(white_balance) if white_balance is not None else None,
                    "metering_mode": str(metering_mode) if metering_mode is not None else None,
                    "resolution": resolution,
                }
            except Exception:
                return {}

        def extract_basic_image_info(path):
            # Resolution for common image formats (works even when there's no EXIF).
            try:
                from PIL import Image

                img = Image.open(path)
                info = {"resolution": f"{img.width}x{img.height}"}
                try:
                    mtime = os.path.getmtime(path)
                    info["captured_time"] = datetime.datetime.fromtimestamp(mtime).isoformat(timespec="seconds")
                    info["captured_time_source"] = "file_time"
                except Exception:
                    pass
                return info
            except Exception:
                return {}

        last_upload_time = None

        for file in files:
            if not file or not file.filename:
                continue
            filename = str(uuid.uuid4()) + "_" + safe_filename(file.filename)
            file_path = os.path.join(CURRENT_FOLDER, filename)
            file.save(file_path)
            try:
                saved_size = os.path.getsize(file_path)
            except Exception:
                saved_size = getattr(file, "content_length", 0) or 0

            meta = {}
            lower_name = file.filename.lower()
            if lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff")):
                meta.update(extract_basic_image_info(file_path))
            if lower_name.endswith((".jpg", ".jpeg", ".tif", ".tiff", ".heic")):
                meta.update(extract_exif_info(file_path))
                if meta.get("date"):
                    meta["captured_time"] = meta.get("date")
                    meta["captured_time_source"] = "exif"

            upload_time = datetime.datetime.now().isoformat()
            last_upload_time = upload_time
            folder_rel = os.path.relpath(CURRENT_FOLDER, UPLOAD_PATH)

            upload_log.append(
                {
                    "filename": filename,
                    "original": file.filename,
                    "size": saved_size,
                    "upload_time": upload_time,
                    "exif": meta,
                    "folder": folder_rel,
                    "full_path": file_path,
                }
            )

            insert_upload(
                filename=filename,
                original=file.filename,
                size=saved_size,
                upload_time=upload_time,
                exif=meta,
                folder=folder_rel,
                full_path=file_path,
                captured_time=meta.get("captured_time"),
                captured_time_source=meta.get("captured_time_source"),
                upload_path=UPLOAD_PATH,
            )

        summary = {"updated": last_upload_time, "total_uploads": len(upload_log), "uploads": upload_log}
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        return "OK"
    except Exception as e:
        return f"Upload error: {e}", 500


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
        files.sort(key=lambda s: s.lower())
        return jsonify({"status": "ok", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.get("/upload-log")
def upload_log_api():
    if not security_ok():
        return jsonify({"status": "unauthorized"}), 401
    try:
        import sqlite3

        limit = request.args.get("limit", "200").strip()
        try:
            limit_n = max(1, min(1000, int(limit)))
        except Exception:
            limit_n = 200

        folder = request.args.get("folder", "").strip()
        if folder and any(c in folder for c in "/\\:><|?*"):
            return jsonify({"status": "error", "error": "Invalid folder name"})

        db_path = get_db_path(UPLOAD_PATH)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if folder:
            c.execute(
                "SELECT id, original, filename, size, upload_time, folder, full_path, exif_date, exif_lat, exif_lon, exif_make, exif_model, exif_resolution, captured_time, captured_time_source FROM uploads WHERE folder = ? ORDER BY id DESC LIMIT ?",
                (folder, limit_n),
            )
        else:
            c.execute(
                "SELECT id, original, filename, size, upload_time, folder, full_path, exif_date, exif_lat, exif_lon, exif_make, exif_model, exif_resolution, captured_time, captured_time_source FROM uploads ORDER BY id DESC LIMIT ?",
                (limit_n,),
            )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({"status": "ok", "uploads": rows})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


if __name__ == "__main__":
    ip = get_ip()
    url = f"http://{ip}:{PORT}/login?token={SECRET_TOKEN}"
    home_url = f"http://{ip}:{PORT}/"

    print("\n========================")
    print("SERVER READY")
    print("PC:   http://127.0.0.1:5000")
    print("PHONE:", url)
    print("========================\n")

    # Open the home page (/) instead of the login QR URL
    threading.Timer(1.5, lambda: webbrowser.open(home_url)).start()
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)
