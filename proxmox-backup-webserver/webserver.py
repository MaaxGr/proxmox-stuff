from flask import Flask, send_file, abort
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD environment variable not set")

# 🔐 Define users and hashed passwords
users = {
    "admin": generate_password_hash(ADMIN_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

BACKUP_SCRIPT = "/srv/proxmox-stuff/prox_config_backup.sh"
BACKUP_FILE = "/mnt/pve/media/backup/pve_backup.tar.gz"

@app.route('/backup', methods=['POST'])
@auth.login_required
def generate_and_serve_backup():
    try:
        subprocess.run([BACKUP_SCRIPT], check=True)

        if os.path.exists(BACKUP_FILE):
            return send_file(
                BACKUP_FILE,
                mimetype='application/gzip',
                as_attachment=True,
                download_name='backup.tar.gz'
            )
            subprocess.run(["rm", BACKUP_FILE], check=True)
        else:
            return abort(500, "Backup file not found.")
    except subprocess.CalledProcessError as e:
        return abort(500, f"Script failed: {e}")
    except Exception as e:
        return abort(500, f"Unexpected error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

