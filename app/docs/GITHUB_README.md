# Paint Lab

**A browser-based painting studio for desktop, tablets, Apple Pencil and experimental creative workflows.**

[Open Paint Lab](https://paint-lab.xyz/) · [Source & releases](https://github.com/sylwesterdigital/paint-lab.xyz) · [Development history](CHANGELOG.md) · [About the project](ABOUT.md) · [Report an issue](https://github.com/sylwesterdigital/paint-lab.xyz/issues)

## Painting studio

Paint Lab is an experimental digital art workspace, not a conventional static drawing pad. Paint with pencil, chalk, watercolour or oil-style pigment; use procedural brush tips or import black/alpha images as reusable tips; draw lines, curves and geometric shapes; combine layers and effects; and save work locally or in an authenticated cloud library.

- **Painting:** material shortcuts, brush shapes, pressure-sensitive stylus input, flow, strength, opacity, wetness, and textured paint simulation.
- **Canvas:** touch and trackpad pan, canvas-only pinch zoom and rotation, paper backgrounds, transparent PNG export, and editable project JSON.
- **Workspace:** movable/resizable panels, undo/redo, draggable quick tools, palettes, four interface themes, and adjustable typography.
- **Projects:** automatic browser draft recovery and IndexedDB gallery; optional server-side private canvases backed by SQLite.
- **Extensibility:** authenticated Flask API, WebSocket project notifications, encrypted AI-provider credentials and connection checks. **AI-generated layer editing is not implemented yet.**

**What’s New** appears once per release until dismissed. Open previous versions at any time with the development-log icon in the top toolbar. The same history lives in [CHANGELOG.md](CHANGELOG.md) and [app/changelog.json](app/changelog.json).


The v0.1.5 palette uses one full-row adaptive grid. Gradient blends use the custom picker as the first stop and the final swatch as the last; Shift-click colours to add intermediate stops. Preset chips transform the active palette without discarding it (Studio restores the default set).

## Technology

The frontend uses HTML, CSS, JavaScript, SVG and Canvas/WebGL-oriented painting techniques. Python/Flask, SQLite in WAL mode, WebSocket notifications, systemd, and nginx support optional hosted canvases. A checksum-validated ZIP watcher manages releases to an isolated Ubuntu service.

```text
app/frontend/index.html          Painting application and version-aware release notes
app/frontend/changelog.json      Public development-log data
app/backend/                    Flask API, SQLite, credentials and WebSocket
app/tests/                      Regression tests and deployment contracts
app/deploy/install.py           Managed Ubuntu/nginx/systemd deployment and rollback
app/changelog.json              Canonical machine-readable release history
app/CHANGELOG.md                Human-readable release history
app/ABOUT.md                    Design vision, boundaries and roadmap
watch-paint-lab.sh              Local versioned release watcher
```

## Development and deployment

Read the detailed [developer and deployment guide](app/README.md) for local setup, authentication, secrets, API test requirements, watcher commands, rollback, DNS, TLS and isolation from other sites. Releases are named `PAINT_LAB_RELEASE_vX.Y.Z.zip` and checked against `manifest.json` SHA-256 digests before deployment. The installer verifies the server and public HTTPS health before the watcher commits and pushes the release to GitHub.

Versioned releases contain the repository documentation sources. When a verified release is complete, the upgraded watcher synchronises this landing page, `ABOUT.md` and `CHANGELOG.md` into the GitHub repository root. It does not overwrite unrelated or locally modified files.

## Links

- [Paint Lab live site](https://paint-lab.xyz/) · [Paint Lab GitHub](https://github.com/sylwesterdigital/paint-lab.xyz) · [Issues and feedback](https://github.com/sylwesterdigital/paint-lab.xyz/issues)
- Related project: [FREE-LAB.cam](https://free-lab.cam/) · [FREE-LAB 3-minute film on YouTube](https://youtu.be/rJ0nFm7jKms) *(FREE-LAB demo, not a Paint Lab demonstration)*

Paint Lab is evolving. Some physically inspired paint effects are artistic approximations rather than fluid simulations; Apple Pencil, Safari and iPad performance need testing on physical hardware.
