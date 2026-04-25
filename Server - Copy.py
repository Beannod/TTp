import os
import uuid
import socket
import threading
import queue
import base64
import io
import html
from flask import Flask, request, jsonify

try:
    import qrcode
except ImportError:
    qrcode = None


UPLOAD_ROOT = r"H:\iPhone photos"
TEMP_FOLDER = os.path.join(UPLOAD_ROOT, "_tmp")

os.makedirs(UPLOAD_ROOT, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

app = Flask(__name__)
PORT = 5000


# -----------------------------
# BACKGROUND QUEUE + STATS
# -----------------------------
upload_queue = queue.Queue()

stats = {"total": 0, "done": 0}


def worker():
    while True:
        item = upload_queue.get()
        if item is None:
            break

        try:
            tmp_path, final_path = item
            os.replace(tmp_path, final_path)

            stats["done"] += 1
            print(f"[DONE] {stats['done']}/{stats['total']}")

        except Exception as e:
            print("[ERROR]", e)

        upload_queue.task_done()


threading.Thread(target=worker, daemon=True).start()


# -----------------------------
# HELPERS
# -----------------------------
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()


def safe(name):
    return os.path.basename(name).replace("/", "_").replace("\\", "_")


def qr(url):
    if not qrcode:
        return ""
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# -----------------------------
# UI
# -----------------------------
def page():
    url = f"http://{get_ip()}:{PORT}"
    qr_img = qr(url)

    qr_html = f"<img src='data:image/png;base64,{qr_img}' style='width:180px;height:180px;'>" if qr_img else ""

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Upload System</title>
</head>

<body style="font-family:Arial; margin:20px;">

<h2>📤 Smart Upload System</h2>

<p><b>Open:</b> {url}</p>
{qr_html}

<hr>

<h3>📁 Create Folder</h3>
<input id="folder" placeholder="folder name">
<button onclick="setFolder()">Set</button>

<p id="current"><b>Current:</b> default</p>

<hr>

<input type="file" id="files" multiple>
<br><br>

<button onclick="upload()">Upload</button>

<h3>Progress</h3>
<p id="progress">Uploaded 0 / 0</p>

<ul id="log"></ul>

<script>

let folder = "default";
let total = 0;
let done = 0;

function setFolder() {{
    let f = document.getElementById("folder").value;
    if (!f) return;
    folder = f;
    document.getElementById("current").innerHTML =
        "<b>Current:</b> " + folder;
}}

function update() {{
    document.getElementById("progress").innerText =
        "Uploaded " + done + " / " + total;
}}

async function upload() {{
    let files = document.getElementById("files").files;
    let log = document.getElementById("log");

    total = files.length;
    done = 0;
    update();

    for (let f of files) {{

        let li = document.createElement("li");
        li.innerText = "Uploading: " + f.name;
        log.appendChild(li);

        let form = new FormData();
        form.append("file", f);
        form.append("folder", folder);

        let res = await fetch("/", {{
            method: "POST",
            body: form
        }});

        if (res.ok) {{
            done++;
            li.innerText = "Queued ✔ " + f.name;
            update();
        }} else {{
            li.innerText = "Failed ❌ " + f.name;
        }}
    }}
}}

</script>

</body>
</html>
"""


# -----------------------------
# ROUTES
# -----------------------------
@app.get("/")
def home():
    return page()


@app.post("/")
def upload():
    file = request.files.get("file")
    folder = request.form.get("folder", "default")

    if not file or not file.filename:
        return jsonify({"status": "no file"}), 400

    filename = safe(file.filename)

    folder_path = os.path.join(UPLOAD_ROOT, folder)
    os.makedirs(folder_path, exist_ok=True)

    tmp_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4()}_{filename}")
    final_path = os.path.join(folder_path, f"{uuid.uuid4()}_{filename}")

    file.save(tmp_path)

    stats["total"] += 1
    upload_queue.put((tmp_path, final_path))

    return jsonify({"status": "queued"})


# -----------------------------
# START SERVER
# -----------------------------
if __name__ == "__main__":
    print("Server running...")
    print(f"Open: http://{get_ip()}:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)