# Paint Lab

**A browser-based painting studio for desktop, tablets, Apple Pencil and experimental creative workflows.**

[Open Paint Lab](https://paint-lab.xyz/) · [Source & releases](https://github.com/sylwesterdigital/paint-lab.xyz) · [Development history](CHANGELOG.md) · [About the project](ABOUT.md) · [Report an issue](https://github.com/sylwesterdigital/paint-lab.xyz/issues)

## Painting studio

Paint Lab is an experimental digital art workspace, not a conventional static drawing pad. Paint with distinctly rendered graphite, crumbly chalk, transparent watercolour washes or opaque ridged oil-style pigment; use procedural brush tips or import black/alpha images as reusable tips; draw lines, curves and geometric shapes; combine layers and effects; and save work locally or in an authenticated cloud library.

- **Painting:** material shortcuts, brush shapes, pressure-sensitive stylus input, flow, strength, opacity, wetness, and textured paint simulation.
- **Canvas:** touch and trackpad pan, canvas-only pinch zoom and rotation, paper backgrounds, transparent PNG export, and editable project JSON.
- **Workspace:** movable/resizable panels, undo/redo, draggable quick tools, palettes, four interface themes, and adjustable typography.
- **Projects:** automatic browser draft recovery and IndexedDB gallery; optional server-side private canvases backed by SQLite.
- **Extensibility:** authenticated Flask API, WebSocket project notifications, encrypted AI-provider credentials and connection checks. **AI-generated layer editing is not implemented yet.**

**What’s New** appears once per release until dismissed. Open previous versions at any time with the development-log icon in the top toolbar. The same history lives in [CHANGELOG.md](CHANGELOG.md) and [app/changelog.json](app/changelog.json).


The v0.1.6 palette uses one full-row adaptive grid. Gradient blends use the custom picker as the first stop and the final swatch as the last; Shift-click colours to add intermediate stops. Preset chips transform the active palette without discarding it (Studio restores the default set).

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


### Mobile studio

Paint Lab v0.1.7 includes a canvas-first phone/tablet workspace: the upper-left focus toggle hides UI, bottom-left quick controls provide colour, brush tip, size and pigment, and the settings cog offers configurable visibility and access to layers, shapes, effects, export and gallery as mobile sheets.


### Safe clearing

Paint Lab v0.1.8 adds a trash-can action on desktop and mobile. Clearing opens a three-choice dialog (cancel, clear, or save a named gallery copy before clearing). The operation preserves canvas dimensions, paper and layers, remains undoable, and does not delete the project history.


### Touch-friendly painting

Paint Lab v0.1.9 introduces a larger vertical brush-size gesture control, active tip previews, bottom-right Undo/Redo and stable pinch-to-zoom without accidental rotation. The mobile menu offers account creation, login and private cloud canvas storage.

## Transforming artwork (v0.1.10)

Press **G** to move, **R** to rotate, or **S** to scale the active painting layer or selected shape. On desktop, no mouse button needs to be held: the artwork immediately follows mouse movement. Left-click or press **Enter** to confirm; **Esc** or right-click to cancel. Press **Shift+D** to duplicate the active layer or selected shape and move the copy before confirming. On phones, use the right-side Move / Rotate / Scale buttons; with a transform active, two-finger gestures manipulate that layer or selected shape. Without a transform active, two-finger pinch/rotate/pan navigates the canvas. Layer operations are recorded in editable history, and duplication is independent of current zoom.

## Mobile gesture stability (v0.1.12)

Navigation now uses a cached document-resolution paint texture with an independent viewport transform: pinch, pan and rotation do not force layer recomposition. The mobile Move/Rotate/Scale controls appear only in an active transform, started from Layers.

### Stroke stylization (v0.1.14)

Brush & Paint → **Stylize** offers halftone, ASCII, inverted-colour, pixel, mosaic and symbol strokes. The stroke effect is separate from Pencil/Chalk/Watercolour/Oil and the artistic tip. Pattern size and strength are configurable and saved with each stroke. Oil freehand now uses a persistent bristle-load contact model: bristles pick up underlying colour, deposit mixed pigment and draw thickness-dependent ridges. The 24 Brush Tips thumbnails share a single cached atlas, rather than using 24 canvases. This is a bounded wet-media 2D approximation, not the full GPU fluid solver. References: [David Li Fluid Paint](https://github.com/dli/paint) (MIT), [Patch Oil Paint](https://patch.gg/blendi/oil-paint) (MIT/CC0).


### v0.1.15 — Workspace appearance and natural brush dynamics

In Studio Settings → Appearance, adjust floating-window borders, transparency, shadows and backdrop blur. In Brush & Paint → Dynamics, enable natural stroke widening and adjust the initial tip contact, growth distance and speed response. Controls persist with workspace presets and individual brush strokes.
