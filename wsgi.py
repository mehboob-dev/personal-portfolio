"""WSGI entrypoint — used by cPanel (Passenger) and `flask run`."""

import os
import sys
from app import create_app
from flask_migrate import upgrade

app = create_app()

# Run DB migrations on every startup (equivalent to `flask db upgrade`).
# Admin user is already synced inside create_app() via _sync_admin_from_secrets().
with app.app_context():
    try:
        basedir = os.path.abspath(os.path.dirname(__file__))
        migrations_dir = os.path.join(basedir, "migrations")
        upgrade(directory=migrations_dir)
        print("Database migrations applied successfully.", file=sys.stdout)
    except Exception as e:
        print(f"Error during automatic database initialization: {e}", file=sys.stderr)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
