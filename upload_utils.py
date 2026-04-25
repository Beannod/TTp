import os
import uuid
from flask import request

def save_uploaded_files(BASE_FOLDER):
    files = request.files.getlist("file")
    folder = request.form.get("folder", "default")
    if not files or not any(f.filename for f in files):
        return "No file"
    folder = "".join(c for c in folder if c.isalnum() or c in "_- ")
    final_path = os.path.join(BASE_FOLDER, folder)
    os.makedirs(final_path, exist_ok=True)
    for file in files:
        if file and file.filename:
            filename = str(uuid.uuid4()) + "_" + os.path.basename(file.filename).replace("/", "_").replace("\\", "_")
            file.save(os.path.join(final_path, filename))
    return "OK"
