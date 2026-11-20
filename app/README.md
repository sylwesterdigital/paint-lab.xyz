# Paint Lab · v0.1.0

A browser painting studio with procedural brush tips, shape tools, multiple layers, local browser gallery, cloud canvas storage, and optional encrypted AI service credentials.

## Structure

- `frontend/index.html` — retained browser editor: layers, painting modes, procedural tips, brush dynamics, multi-touch input, draggable panels, palettes, IndexedDB gallery, and cloud canvas UI.
- `backend/app.py` — Flask API with account registration/login, authenticated private canvas CRUD, provider-key management, and `/ws` notifications.
- `backend/db.py` — SQLite WAL database with users, project documents, and encrypted provider-key records.
- `backend/keyvault.py` — per-user encrypted keys (Fernet); vault key lives outside releases.
- `deploy/install.py` — Ubuntu nginx + systemd setup with certificate bootstrap and safe rollback.
- `tests/` — HTTP, SQLite, authentication, encryption and deployment-contract tests.

The browser editor also works without the backend, using IndexedDB. Cloud saving and provider settings require an active Flask API and an account. Project JSON uses the existing `paint-lab-webgl` format with a full editable action history. No AI inference/layer regeneration is executed by this release; provider credentials and connection tests are an infrastructure foundation for future explicit AI actions.

## Local development

From `app/`:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m backend.app
```

Open `http://127.0.0.1:18766/`. SQLite data defaults to `app/var/` locally; override with `PAINT_LAB_DATA_DIR`. Never commit the local database, vault key, or environment secrets.

## Release and Ubuntu deployment

The release package `PAINT_LAB_RELEASE_vX.Y.Z.zip` is self-contained and includes a `manifest.json` with SHA-256 digests and `watch-paint-lab.sh`.

1. Place `watch-paint-lab.sh` in the root of your cloned `git@github.com:sylwesterdigital/paint-lab.xyz.git` repository (branch `main`), and make it executable.
2. Place the ZIP under `updates/` or `uploads/` in that root.
3. `./watch-paint-lab.sh --dry-run` validates the release without contacting GitHub, SSH, or the server.
4. Set `PAINT_LAB_CERTBOT_EMAIL` if a Let's Encrypt certificate does not already exist. Then `./watch-paint-lab.sh --once`, or run `./watch-paint-lab.sh` continuously.

Watcher environment variables:

| Name | Default | Purpose |
| --- | --- | --- |
| `PAINT_LAB_SSH_HOST` | `root@46.62.232.64` | SSH destination from FREE-LAB reference; change if Paint Lab is deployed elsewhere |
| `PAINT_LAB_SSH_PORT` | `333` | SSH port from FREE-LAB reference |
| `PAINT_LAB_EXPECTED_IP` | `46.62.232.64` | Required DNS A-record match before the installer modifies the server |
| `PAINT_LAB_CERTBOT_EMAIL` | unset | Required for initial TLS issuance; existing certificate needs no email |
| `PAINT_LAB_INSTALL_PACKAGES` | `1` | Allow installation of missing Ubuntu packages only |
| `PAINT_LAB_PUBLIC_URL` | `https://paint-lab.xyz/` | Public verification address |

`--status`, `--tail`, `--diagnose`, and `--rollback` are supported. The watcher refuses a dirty Git worktree, wrong Git origin, incorrect checksum/version, unsafe ZIP, unsafe SSH target, and a conflicting nginx virtual host. It stages via SSH, tests in the release context, switches an atomic release symlink, checks localhost Flask/SQLite health, checks public HTTPS, and only then commits/pushes the release to GitHub `main`.

**First deployment requires:** DNS `paint-lab.xyz` pointed at the intended Ubuntu server, key-based root SSH with a trusted host key, port 80/443 reachable for certbot, and a real email for Let's Encrypt when the certificate is absent. SSH, DNS, firewall and TLS have **not** been tested on the user's live server by this generated release. If nginx already serves `paint-lab.xyz` from an unmanaged configuration, deployment **stops** rather than rewriting it.

### Server isolation

- nginx vhost: `/etc/nginx/sites-available/paint-lab.xyz`
- systemd: `paint-lab.service`
- loopback backend: `127.0.0.1:18766` (separate from FREE-LAB's 18765)
- releases: `/var/www/paint-lab.xyz/releases/vX.Y.Z/`
- live symlink: `/var/www/paint-lab.xyz/current`
- persistent SQLite: `/var/lib/paint-lab/paint-lab.sqlite3`
- persistent encrypted secrets: `/etc/paint-lab-vault.key` (root-owned, readable by `paint-lab` group)
- persistent session secret: `/etc/paint-lab.env`

### Security boundaries

Provider API keys are **never sent back** after saving or added to artwork/project exports. Users must authenticate to access their projects and their provider keys. The API uses HTTP-only SameSite cookies, CSRF protection, ownership-filtered SQL queries, a 16 MB project limit, and restricted known-provider HTTPS verification endpoints. WebSocket events are authenticated and same-origin, and are limited to project update notifications in this release. The WebSocket broadcast design uses one threaded Gunicorn worker, not a distributed message queue.

For production public sign-ups, add email verification, password recovery, account deletion, service-level rate limiting, DB backup/restore automation, and monitoring before inviting untrusted users at scale. SQLite backups should include WAL-consistent snapshots (e.g. SQLite backup API), stored separately from deployments. The installer intentionally never rolls back the database.

### Version upgrades

Bump `app/version.json`, `app/frontend/version.json`, the `<meta name="paint-lab-version">` tag in `frontend/index.html`, and `app/changelog.json`; run `python3 app/tools/build_release.py` from the repository root to generate a new SHA-256-manifest release ZIP in `updates/`. The watcher itself has a separate `VERSION` marker and requires a watcher version bump if its content changes in a later release.

## v0.1.1: Existing Certbot account reuse and coloured releases

On Ubuntu, the installer checks whether a certificate for `paint-lab.xyz` already exists. If not, it looks for an existing production Let’s Encrypt account in `/etc/letsencrypt/accounts/acme-v02.api.letsencrypt.org/directory/` and uses that account to request a separate certificate for Paint Lab; no email is required when an account is present. The optional `PAINT_LAB_CERTBOT_ACCOUNT` chooses a specific existing account. If this server has no existing production account, define `PAINT_LAB_CERTBOT_EMAIL` for first-time registration. DNS and nginx collision checks run before any vhost is modified.

The watcher uses automatic ANSI colour on interactive terminals, with high-visibility start/success/failure banners. Set `NO_COLOR=1` to disable colours or `FORCE_COLOR=1` to enable colours in output captured by another program. Persistent release logs are always plain text.
