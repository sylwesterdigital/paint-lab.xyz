"""Server-side, operator-only Paint Lab administrator provisioning.

From a trusted shell on Ubuntu:
  cd /var/www/paint-lab.xyz/current
  sudo -u paint-lab env PAINT_LAB_DB=/var/lib/paint-lab/paint-lab.sqlite3 \
    /opt/paint-lab/venv/bin/python -m backend.admin_cli promote EXISTING_USERNAME
  # or: ... -m backend.admin_cli create NEW_USERNAME

No default admin passwords, browser-side promotion, or network-based role changes.
"""
from __future__ import annotations
import argparse,getpass,os,re,sqlite3,sys
from pathlib import Path
from werkzeug.security import generate_password_hash
from . import db

def main(argv=None):
    p=argparse.ArgumentParser(description='Provision Paint Lab administrator from a trusted server shell')
    p.add_argument('action',choices=('create','promote'))
    p.add_argument('username')
    args=p.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,40}',args.username):p.error('Invalid username')
    path=Path(os.environ.get('PAINT_LAB_DB','/var/lib/paint-lab/paint-lab.sqlite3'))
    if not path.is_file():p.error('Expected an existing Paint Lab database; refusing to create a new one')
    with db.connect(path) as con:
        if args.action=='promote':
            cursor=con.execute("UPDATE users SET role='admin' WHERE username=?",(args.username,))
            if cursor.rowcount!=1:p.error('Existing user not found; create an account first')
        else:
            password=getpass.getpass('New administrator password (16+ characters): ')
            if len(password)<16 or len(password)>256:p.error('Password must be 16–256 characters')
            if password!=getpass.getpass('Confirm password: '):p.error('Passwords did not match')
            try:
                con.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,'admin')",(args.username,generate_password_hash(password)))
            except sqlite3.IntegrityError:p.error('Username already exists; use promote')
    print('Administrator account configured:',args.username)
    return 0
if __name__=='__main__':sys.exit(main())
