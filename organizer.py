import os
import shutil
import time
import hashlib
from pathlib import Path
import mimetypes
from datetime import datetime

# Basic categories (you can extend)
FILE_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".csv"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Music": [".mp3", ".wav", ".aac", ".flac"],
    "Archives": [".zip", ".rar", ".tar", ".gz"],
}

def get_category(extension: str) -> str:
    """Return category name for an extension, or 'Others'."""
    ext = extension.lower()
    for cat, exts in FILE_CATEGORIES.items():
        if ext in exts:
            return cat
    mime = mimetypes.guess_type("file" + ext)[0]
    if mime:
        main_type = mime.split("/")[0]
        if main_type in ["image", "video", "audio"]:
            return main_type.capitalize() + "s"
    return "Others"

def calculate_hash(filepath, block_size=65536):
    """Calculates the MD5 hash of a file."""
    try:
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
    except Exception:
        return None 

def get_destination_path(folder: Path, file: Path, category: str, organize_mode: str) -> Path:
    """
    Creates the destination path based on the chosen organization mode.
    Mode options: 'Category Only', 'Category / Year', 'Category / Year-Month'
    """
    if organize_mode == "Category Only":
        return folder / category
    
    # Get file modification date/time
    timestamp = file.stat().st_mtime
    dt_object = datetime.fromtimestamp(timestamp)
    year = dt_object.strftime("%Y")
    month_year = dt_object.strftime("%Y-%m") # e.g., 2024-07

    if organize_mode == "Category / Year":
        return folder / category / year
    
    if organize_mode == "Category / Year-Month":
        return folder / category / month_year
    
    return folder / category


def organize_files(folder_path, organize_mode: str, check_duplicates: bool, progress_callback=None):
    """
    Organize files in folder_path with duplicate removal and advanced mode options.
    """
    start = time.time()
    folder = Path(folder_path)
    # Exclude folders, and main script files
    files = [f for f in folder.iterdir() if f.is_file() and f.name not in ["app.py", "organizer.py"]]
    total = len(files)

    logs = []
    seen_hashes = {}
    duplicate_files = 0
    space_saved_bytes = 0

    analytics = {
        "total_files": total,
        "total_size_bytes": 0,
        "categories": {}, 
        "time_taken_sec": 0.0,
        "duplicates_removed": 0,
        "space_saved_bytes": 0,
        "logs": [] 
    }

    if total == 0:
        analytics["time_taken_sec"] = round(time.time() - start, 3)
        if progress_callback:
            progress_callback(100, "No files to organize")
        return logs, analytics

    for i, file in enumerate(files, start=1):
        log_entry = ""
        try:
            ext = file.suffix
            size = file.stat().st_size
            analytics["total_size_bytes"] += size
            
            # --- 1. Duplicate Check Logic ---
            if check_duplicates:
                file_hash = calculate_hash(file)
                if file_hash is None:
                    log_entry = f"Warning: Could not read hash for {file.name}. Skipping duplicate check."
                elif file_hash in seen_hashes:
                    # Found a duplicate!
                    duplicate_files += 1
                    space_saved_bytes += size
                    
                    # Create Duplicates folder and move
                    duplicate_dir = folder / "Duplicates (Removed)"
                    duplicate_dir.mkdir(exist_ok=True)
                    shutil.move(str(file), duplicate_dir / file.name)
                    log_entry = f"DUPLICATE REMOVED: {file.name} -> Duplicates"
                    
                    analytics["logs"].append(log_entry)
                    if progress_callback:
                        progress_callback(int((i / total) * 100), log_entry)
                    continue 
                else:
                    seen_hashes[file_hash] = file.name 

            # --- 2. Organization Logic ---
            category = get_category(ext)
            analytics["categories"].setdefault(category, 0)
            analytics["categories"][category] += 1

            # Get dynamic destination path based on mode
            dest_dir = get_destination_path(folder, file, category, organize_mode)
            dest_dir.mkdir(parents=True, exist_ok=True) 
            
            shutil.move(str(file), dest_dir / file.name)

            log_entry = f"Moved: {file.name} → {dest_dir.relative_to(folder)}"
        except Exception as e:
            log_entry = f"ERROR moving {file.name}: {e}"

        # Report progress and log
        analytics["logs"].append(log_entry)
        if progress_callback and total:
            percent = int((i / total) * 100)
            progress_callback(percent, f"Processing {file.name} ({i}/{total})")

    # Final analytics update
    analytics["time_taken_sec"] = round(time.time() - start, 3)
    analytics["duplicates_removed"] = duplicate_files
    analytics["space_saved_bytes"] = space_saved_bytes

    if progress_callback:
        progress_callback(100, f"Completed — {analytics['total_files']} files organized.")

    # Return the full log list and analytics dictionary
    return analytics["logs"], analytics