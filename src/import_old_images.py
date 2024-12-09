from pathlib import Path
import sqlite3
import hashlib
from lib.image_helper import add_image

backup_path = Path("../backupImages")
server_id = 556672124559949835
conn = sqlite3.connect(Path("../data") / "db" / "keabot.sqlite3")
for x in backup_path.glob("*"):
    tag = x.stem
    for image in x.glob("*"):
        attachment_content = image.read_bytes()
        file_hash = hashlib.sha256(attachment_content).hexdigest()
        ext = image.suffix
        new_filename = f"{file_hash}{ext}"
        file_path = Path("../data") / "images" / new_filename

        file_path.write_bytes(attachment_content)
        add_image(conn, server_id, [tag], new_filename)