import os
import time

import re
import bcrypt
from dotenv import load_dotenv
load_dotenv("secrets.env")


timestr = time.strftime("%Y-%m-%d")

# ensure the memo_uploads folder is created in the same directory as the script.
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)  # Gets the absolute path of the current Python file.
UPLOAD_DIR = os.path.join(
    BASE_DIR, "memo_uploads"
)  # Combines the base path with 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)  # ensure uploads folder exists


def sanitize_filename(filename: str) -> str:
    # Remove path separators and dangerous characters
    name = re.sub(r'[<>:"/\\|?*]', "", filename)
    return name[:50]  # Limit length


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

hash = bcrypt.hashpw(os.getenv("UPLOAD_PASSWORD").encode('utf-8'), bcrypt.gensalt())