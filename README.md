# Secure File Uploader

A modern, secure, multi-file uploader and gallery web app built with Python (Flask) and HTML/JS, supporting all file types, folder management, persistent logging, EXIF extraction, and in-app updates.

## Features
- **Multi-file upload** with drag-and-drop and progress display
- **Folder management**: create and switch folders for uploads
- **Gallery view**: Google Photos-like grid for images and files
- **EXIF extraction**: For images, metadata is extracted and logged
- **Persistent logging**: All uploads are logged to both JSON and SQLite (with full file path)
- **In-app update**: Secure endpoint to pull latest code from GitHub
- **Session-based login**: QR login and password
- **Modern UI**: Responsive, compact, and user-friendly

## Project Structure
```
config.json
Server.py
Start.bat
FILES/
uploads/
  _tmp/
  <folders>/
db.py
upload.html
login.html
uploads_log.json
uploads.db
```

## Getting Started
1. **Install dependencies**
   - Python 3.x
   - Flask
   - Pillow
   - piexif
   - qrcode

   Install with pip:
   ```sh
   pip install flask pillow piexif qrcode
   ```

2. **Start the server**
   - On Windows (PowerShell):
     ```sh
     .\Start.bat
     ```
   - Or directly:
     ```sh
     python Server.py
     ```

3. **Login**
   - Scan the QR code or use the password (default: `binod`)

4. **Upload files**
   - Use the web UI at http://127.0.0.1:5000
   - Create folders, upload files, view gallery

5. **Update app**
   - Use the "Update App" button in the UI (admin only)

## Logging
- All uploads are logged to `uploads_log.json` and `uploads.db` (SQLite)
- Each log entry includes filename, original name, size, upload time, EXIF (if image), folder, and full file path

## Security
- Only authenticated users on the local network can upload or update
- Update endpoint is protected and only accessible to admins

## Customization
- Change upload base path and folder at startup
- Edit `Server.py` and `upload.html` for UI or backend changes

## License
MIT
