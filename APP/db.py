import sqlite3
import os
from datetime import datetime


def get_db_path(upload_path):
    return os.path.join(upload_path, "uploads.db")

def init_db(upload_path):
    db_path = get_db_path(upload_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            original TEXT,
            size INTEGER,
            upload_time TEXT,
            exif_date TEXT,
            exif_lat REAL,
            exif_lon REAL,
            exif_make TEXT,
            exif_model TEXT,
            exif_orientation TEXT,
            exif_exposure TEXT,
            exif_iso TEXT,
            exif_focal_length TEXT,
            exif_software TEXT,
            exif_lens_model TEXT,
            exif_aperture TEXT,
            exif_flash TEXT,
            exif_white_balance TEXT,
            exif_metering_mode TEXT,
            exif_resolution TEXT,
            folder TEXT,
            full_path TEXT,
            captured_time TEXT,
            captured_time_source TEXT
        )
    ''')
    # Backward-compatible migration for older DBs.
    try:
        c.execute("PRAGMA table_info(uploads)")
        cols = {row[1] for row in c.fetchall()}
        if "full_path" not in cols:
            c.execute("ALTER TABLE uploads ADD COLUMN full_path TEXT")
        if "captured_time" not in cols:
            c.execute("ALTER TABLE uploads ADD COLUMN captured_time TEXT")
        if "captured_time_source" not in cols:
            c.execute("ALTER TABLE uploads ADD COLUMN captured_time_source TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()

def insert_upload(filename, original, size, upload_time, exif, folder, full_path, captured_time, captured_time_source, upload_path):
    db_path = get_db_path(upload_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO uploads (
            filename, original, size, upload_time, exif_date, exif_lat, exif_lon,
            exif_make, exif_model, exif_orientation, exif_exposure, exif_iso, exif_focal_length,
            exif_software, exif_lens_model, exif_aperture, exif_flash, exif_white_balance, exif_metering_mode, exif_resolution, folder, full_path, captured_time, captured_time_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        original,
        size,
        upload_time,
        exif.get('date'),
        exif.get('lat'),
        exif.get('lon'),
        exif.get('make'),
        exif.get('model'),
        exif.get('orientation'),
        exif.get('exposure'),
        exif.get('iso'),
        exif.get('focal_length'),
        exif.get('software'),
        exif.get('lens_model'),
        exif.get('aperture'),
        exif.get('flash'),
        exif.get('white_balance'),
        exif.get('metering_mode'),
        exif.get('resolution'),
        folder,
        full_path,
        captured_time,
        captured_time_source
    ))
    conn.commit()
    conn.close()

def get_all_uploads(upload_path):
    db_path = get_db_path(upload_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM uploads ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return rows
