# Paint Lab · v0.1.16

A browser painting studio with procedural brush tips, shape tools, multiple layers, local browser gallery, cloud canvas storage, and optional encrypted AI service credentials.

[Open Paint Lab](https://paint-lab.xyz/) · [Project story](ABOUT.md) · [Changelog](CHANGELOG.md) · [GitHub](https://github.com/sylwesterdigital/paint-lab.xyz)

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

Bump `app/version.json`, `app/frontend/version.json`, the `<meta name="paint-lab-version">` tag in `frontend/index.html`, `app/changelog.json`, and `app/frontend/changelog.json`; run `python3 app/tools/build_release.py` from the repository root to generate a new SHA-256-manifest release ZIP in `updates/`. The watcher itself has a separate `VERSION` marker and requires a watcher version bump if its content changes in a later release.

## v0.1.1: Existing Certbot account reuse and coloured releases

On Ubuntu, the installer checks whether a certificate for `paint-lab.xyz` already exists. If not, it looks for an existing production Let’s Encrypt account in `/etc/letsencrypt/accounts/acme-v02.api.letsencrypt.org/directory/` and uses that account to request a separate certificate for Paint Lab; no email is required when an account is present. The optional `PAINT_LAB_CERTBOT_ACCOUNT` chooses a specific existing account. If this server has no existing production account, define `PAINT_LAB_CERTBOT_EMAIL` for first-time registration. DNS and nginx collision checks run before any vhost is modified.

The watcher uses automatic ANSI colour on interactive terminals, with high-visibility start/success/failure banners. Set `NO_COLOR=1` to disable colours or `FORCE_COLOR=1` to enable colours in output captured by another program. Persistent release logs are always plain text.

## v0.1.2: Native SVG controls and desktop keyboard help

Controls use embedded, theme-aware SVG symbols drawn from the supplied icon pack. No external icon font or network dependency. Keyboard help opens with Command+/ or Ctrl+/ and also Command+Shift+/ for `?` on supported layouts. Shortcuts remain available via the help toolbar button.

## v0.1.3: Fast artist workflow and reusable brush masks

Choose Pencil, Chalk, Watercolour or Oil directly on the draggable tool rail (keyboard shortcuts 1–4). The canvas-only status chip always shows painting mode/effect, pigment, tip, selected colour, brush diameter and zoom. The palette starts with a native colour-picker swatch, then colour chips; preset and generator controls are intentionally compact.

Brush tips use category filters (Dots, Liners, Flats, Rakes, Textures and Custom) and larger picture previews. Upload a black-and-transparent PNG (or an image with dark strokes) to create a brush mask, or capture visible painted pixels from the current canvas. Imported 96×96 alpha masks are embedded in named settings presets and editable project JSON, avoiding external asset dependencies. A maximum of 28 custom tips applies per workspace. Large image uploads are rejected.

Layer add, duplicate, delete, property edits, and order changes now update the live layer stack directly instead of replaying every stroke. Layer previews are drawn directly into thumbnail canvases, with active-layer updates throttled after strokes. Long history lists are paged in the UI, while the complete history remains editable. Undo/redo and project restores still replay the editable action history.

## v0.1.4: Public development log and project documentation

The painting application checks `frontend/changelog.json` against the HTML version marker on load, displays What's New only when that version has not been dismissed in the current browser, and provides a permanent toolbar control to reopen the Latest and History tabs. No authentication or server API is required for the log. A bundled fallback allows direct-file previews. The dismissed version is stored as a small localStorage value.

`app/changelog.json` and `app/frontend/changelog.json` must match. Bump version markers, update both data files, edit `ABOUT.md`, `CHANGELOG.md` and `docs/GITHUB_README.md`, then build the ZIP. The release watcher verifies that these documents exist and synchronises the canonical project documents into the GitHub repo root after a verified deployment and successful source commit. The watcher refuses to overwrite untracked user documents or local edits.

If v0.1.4 is first deployed using an older watcher in `--once` mode, the new watcher script will be installed, but automatic repo-root documentation sync requires starting the upgraded watcher again or using `./watch-paint-lab.sh --publish-docs`. For a continuously running watcher, the upgraded watcher reloads and performs the sync automatically. This never changes the Ubuntu installation.

Only verified public links are used: the [live Paint Lab site](https://paint-lab.xyz/), [GitHub repository](https://github.com/sylwesterdigital/paint-lab.xyz) and [issues](https://github.com/sylwesterdigital/paint-lab.xyz/issues). The [FREE-LAB YouTube film](https://youtu.be/rJ0nFm7jKms) is linked clearly as a related-project example, not as a Paint Lab film.

## Palette workflow (v0.1.6)

The custom colour picker occupies the first swatch. The grid automatically lays out every colour when panels are resized. Studio restores factory colours; Pastels, Sharp, Chromatics, Sepias and additional colour modifiers act on the current palette. Gradients interpolate in OKLab from the current colour through optional Shift-click intermediate anchors to the final swatch.


### Mobile canvas-first workspace (v0.1.7)

On coarse-pointer devices up to 1024px wide, Paint Lab opens as a full-canvas touch workspace instead of showing floating desktop panels. The top-left eye/brush toggle hides all painting controls for focused drawing; tapping it again restores them. The bottom-left colour swatch opens a slim edge palette with a preset-cycle and custom-colour picker. Tap the brush icon to cycle tips or the size number to open a vertical brush-diameter slider. The pigment button cycles Pencil, Chalk, Watercolour and Oil. The top-right cog opens mobile Settings, where users can choose which quick controls stay visible and open the full desktop tools as temporary mobile sheets. The top-right save action opens the existing named local gallery save dialog. These mobile preferences persist independently from desktop workspace positions.


### Safe clearing

Paint Lab v0.1.8 adds a trash-can action on desktop and mobile. Clearing opens a three-choice dialog (cancel, clear, or save a named gallery copy before clearing). The operation preserves canvas dimensions, paper and layers, remains undoable, and does not delete the project history.


### Mobile workflow (v0.1.9)

On touch devices the canvas-first studio provides an actual brush-tip preview above the colour swatch, a draggable vertical brush-diameter control, and Undo / Redo in the bottom-right corner. A mobile setting allows intentional two-finger rotation; this is off by default to prevent accidental paper tilt. Pinch zoom and pan are always available. The **Account & profile** section connects to private server canvases and login/registration.

## Transforming artwork (v0.1.10)

Press **G** to move, **R** to rotate, or **S** to scale the active painting layer or selected shape. **No click-and-drag is needed on desktop:** move the mouse to preview, left-click or press **Enter** to apply, and **Esc** (or right-click) to cancel. Press **Shift+D** to duplicate the active layer or selected shape and move the duplicate immediately before confirming. On phones, use the right-side Move / Rotate / Scale buttons; with a transform active, two-finger gestures manipulate that layer or selected shape. Without a transform active, two-finger pinch/rotate/pan navigates the canvas. Layer operations are recorded in editable history, and duplication is independent of current zoom.

## Mobile gesture stability (v0.1.12)

Navigation now uses a cached document-resolution paint texture with an independent viewport transform: pinch, pan and rotation do not force layer recomposition. The mobile Move/Rotate/Scale controls appear only in an active transform, started from Layers.

### Stroke stylization (v0.1.14)

Brush & Paint → **Stylize** offers halftone, ASCII, inverted-colour, pixel, mosaic and symbol strokes. The stroke effect is separate from Pencil/Chalk/Watercolour/Oil and the artistic tip. Pattern size and strength are configurable and saved with each stroke. Oil freehand now uses a persistent bristle-load contact model: bristles pick up underlying colour, deposit mixed pigment and draw thickness-dependent ridges. The 24 Brush Tips thumbnails share a single cached atlas, rather than using 24 canvases. This is a bounded wet-media 2D approximation, not the full GPU fluid solver. References: [David Li Fluid Paint](https://github.com/dli/paint) (MIT), [Patch Oil Paint](https://patch.gg/blendi/oil-paint) (MIT/CC0).


### v0.1.15 — Workspace appearance and natural brush dynamics

In Studio Settings → Appearance, adjust floating-window borders, transparency, shadows and backdrop blur. In Brush & Paint → Dynamics, enable natural stroke widening and adjust the initial tip contact, growth distance and speed response. Controls persist with workspace presets and individual brush strokes.

## v0.1.16 — Brush contacts and diagnostics

The oil renderer now samples the selected brush tip silhouette (including imported alpha masks) into a cached bristle-contact profile. A liner, flat, fan, rake, mop or pointed tip changes the real stroke footprint and pigment placement, not merely its icon or UI label. Pencil, chalk and watercolour continue to use material-specific pigment textures. This is still a 2-D painterly approximation, not a full fluid-dynamics simulation.

Startup release notes render immediately from bundled data. Local recovery shows progress and replays stored marks in bounded animation-frame batches without a full blocking replay. A slow server no longer prevents the development log from appearing.

The administrator-only server diagnostics console can be opened after login. It displays bounded application log entries, request latencies and error totals, with font size adjustment and pause. It deliberately does not expose OS journal logs or sensitive HTTP request bodies, API keys, cookies and passwords.

**Provisioning an admin account:** All newly registered accounts receive the `user` role. On a trusted Ubuntu server shell, promote an existing account with:

```sh
cd /var/www/paint-lab.xyz/current
sudo -u paint-lab env PAINT_LAB_DB=/var/lib/paint-lab/paint-lab.sqlite3 \
  /opt/paint-lab/venv/bin/python -m backend.admin_cli promote EXISTING_USERNAME
```

Or use `create USERNAME` (password prompted interactively) from a trusted shell. No default administrator account or password is deployed, and users cannot assign admin roles from the browser. A pre-existing SQLite users table is migrated to include the new `role` column without deleting existing accounts or paintings.
