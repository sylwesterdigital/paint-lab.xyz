# Paint Lab

**A browser-based painting studio for desktop, tablets, Apple Pencil and experimental creative workflows.**

[Open Paint Lab](https://paint-lab.xyz/) · [Source & releases](https://github.com/sylwesterdigital/paint-lab.xyz) · [Development history](CHANGELOG.md) · [About the project](ABOUT.md) · [Report an issue](https://github.com/sylwesterdigital/paint-lab.xyz/issues)

## Painting studio

Paint Lab is an experimental digital art workspace, not a conventional static drawing pad. Paint with distinctly rendered graphite, crumbly chalk, transparent watercolour washes or opaque ridged oil-style pigment; use procedural brush tips or import black/alpha images as reusable tips; draw lines, curves and geometric shapes; combine layers and effects; and save work locally or in an authenticated cloud library.

- **Layers:** Finder-style multi-selection (Shift-click ranges, Command/Ctrl-click disjoint rows), group visibility/duplication/deletion, and raster merge selected/all. All operations are undoable.
- **Painting:** material shortcuts, brush shapes, pressure-sensitive stylus input, flow, strength, opacity, wetness, and textured paint simulation.
- **Canvas:** touch and trackpad pan, canvas-only pinch zoom and rotation, paper backgrounds, transparent PNG export, and editable project JSON.
- **Workspace:** movable/resizable panels, undo/redo, draggable quick tools, palettes, four interface themes, and adjustable typography.
- **Projects:** automatic browser draft recovery and a responsive, native-aspect masonry IndexedDB gallery with local search, date filters and editing; optional server-side private canvases backed by SQLite.
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

### Stroke-masked image reveal filters (v0.1.36)

In Brush & Paint → **Stylize**, choose Pixel, Halftone, ASCII, Symbols, Mosaic, Invert or another conversion filter, then brush over **already-existing artwork**. The brush pressure and tip determine a reveal mask; the filter reads the *existing visible image* under the mask, not newly deposited pigment. A transparent empty area stays empty. New stroke actions record `existing-image-fx-v3` for replay and undo/redo, while pre-0.1.36 saved stylization actions retain their historical appearance. Filter patterns stay aligned to document coordinates. The brush engine remains a 2D raster approximation, not a GPU pigment solver.

### Stroke stylization (v0.1.14)

Brush & Paint → **Stylize** offers halftone, ASCII, inverted-colour, pixel, mosaic and symbol strokes. The stroke effect is separate from Pencil/Chalk/Watercolour/Oil and the artistic tip. Pattern size and strength are configurable and saved with each stroke. Oil freehand now uses a persistent bristle-load contact model: bristles pick up underlying colour, deposit mixed pigment and draw thickness-dependent ridges. The 24 Brush Tips thumbnails share a single cached atlas, rather than using 24 canvases. This is a bounded wet-media 2D approximation, not the full GPU fluid solver. References: [David Li Fluid Paint](https://github.com/dli/paint) (MIT), [Patch Oil Paint](https://patch.gg/blendi/oil-paint) (MIT/CC0).


### v0.1.15 — Workspace appearance and natural brush dynamics

In Studio Settings → Appearance, adjust floating-window borders, transparency, shadows and backdrop blur. In Brush & Paint → Dynamics, enable natural stroke widening and adjust the initial tip contact, growth distance and speed response. Controls persist with workspace presets and individual brush strokes.

## v0.1.16 — Improved brush fidelity and diagnostics

Oil painting now uses each artistic tip's actual physical contact profile: liner, fan, rake, flat and imported brush masks leave different strokes. Development notes appear without waiting for a remote response, and saved-browser recovery reports its progress. The server now provides an administrator-only operational log terminal with role-gated access, request timings and bounded log output. Administrator accounts must be provisioned from the trusted server shell; none is created with a default password.

## Portable art and publishing (v0.1.23)

Choose Window size, preset aspect ratios, or custom pixel dimensions when creating a canvas. Download layered editable `.paintlab.zip` files (document JSON, per-layer PNGs, imported brush assets, preview), export transparent or paper-backed PNGs, and import the bundles later. Share an image through the native Web Share API when available. Account holders can optionally publish only a rendered image to a revocable public URL and a username gallery; private project files, layer histories and API keys remain private.

### Palette sizes and movement-driven colour flow (v0.1.23)

The Palette header supports **XL** (8 large swatches), **M** (24), and **S** (48 smaller swatches). Switching size retains the underlying palette; extra small swatches are generated by perceptual interpolation. The **Flow** switch, next to the harmony generator, advances brush pigment through the selected palette only as the pointer travels. The selection and sampled colours are captured per stroke for deterministic Undo/Redo and reopening; the setting is also stored in workspace presets.


## Mobile touch and painting (v0.1.26)

Multi-touch gestures exclusively pan, pinch, and rotate the canvas while two fingers are down. The remaining finger stays navigation-only until all contacts are released. Oil brushes now start and end without the artificial bristle-fan star; active swatches and tips have strong selection markers.

## v0.1.30 release integrity

The development-log UI must match the running release version, even when offline. The deterministic release builder and watcher v0.1.4 reject embedded/history mismatches, and the browser smoke test opens the actual dialog. New oil strokes also interpolate sparse pointer samples and use bounded endpoint tiles on high-resolution canvases; legacy stroke actions are replayed unchanged. The painting engine remains a raster approximation; independent GPU pigment and height buffers are still research.

### Live project donations (v0.1.66)

The painting studio’s top-left **Paint-lab v0.1.66** text identity includes [GitHub](https://github.com/sylwesterdigital/paint-lab.xyz) and **Donate**. The public artwork viewer’s **Download & Support** panel keeps the original PNG download free and offers the same optional donation route. The support dialogs contain the official Stripe Buy Button supplied by the project operator and an [independent Stripe-hosted Payment Link](https://donate.stripe.com/4gM6oGbw61Wf5nJa1wcZa0c) in case embeds or scripts are blocked. The button activates only when someone opens a support dialog; payment and any subsequent checkout redirects are handled by Stripe.

No secret key or webhook secret is included in the release; only Stripe’s client-safe `pk_live_…` identifier and public buy-button ID are exposed. The older `POST /api/support/checkout` and `/api/stripe/webhook` routes remain separate, optional server-side integrations: they still require secret configuration. **Payments made through the new Payment Link do not automatically populate the app’s `support_payments` SQLite table**; reconcile these in the Stripe dashboard unless a verified Payment Link webhook integration is developed later. Donations are to Paint Lab, not individual artists or a payout system.


## v0.1.67 — Desktop workspace controls

The desktop app bar now shows a three-dot overflow and Settings cog with Clear, Save, Undo and Redo pinned by default. Settings → Desktop toolbar quick actions lets you choose any toolbar action to keep visible; this choice is saved with workspace settings and named presets. The canvas HUD shows current zoom and a Fit control; **Shift+S** opens Save & share. Floating desktop windows stay below the Paint-lab wordmark and header actions. Existing free downloads and optional project donations are unchanged.

## v0.1.68 — Brush selection and panel positioning

The desktop Brush Tips window prioritizes visible, scrollable silhouettes. Advanced brush editing and text/character stamping are expandable sections, closed by default. Collapsed draggable windows can be positioned 6 px from the viewport's top edge, independently of the expanded-panel header allowance. GitHub and Donate use plain black, shadow-free text. No painting data or payment behaviour changes.

## v0.1.69 — Fast layered gallery saves

Local Save & share now saves PNG-backed layers by default without preserving earlier brush strokes; the **Keep brush stroke history** checkbox preserves the editable stroke sequence and prior Undo states. Both choices open from layer snapshots without replaying the painting. Previously saved history-only artworks are still supported and will preserve their history by default when reopened. A public gallery link is available beside GitHub and Donate in the studio header. Flattened-layer artwork retains its own layer stack and can accept new edits and Undo history.

## v0.1.70 — Public artwork sharing and Rantlist

Save & share now offers **Save & Publish**, which creates a new editable local gallery copy and then publishes the visible PNG with a single click; this never silently overwrites an existing saved artwork. After publishing, **Open link** opens the public artwork alongside Copy link. **Share to Rantlist #lobby** is opt-in. Until Rantlist deploys its authenticated bot receiver it copies the publication URL and opens Rantlist for manual posting; it never claims the chat message was sent. The separate signed server-to-server bot bridge is fully specified in [Rantlist integration](app/docs/RANTLIST_INTEGRATION.md) and disabled until server secrets are configured. No private project history or login data is shared.

## v0.1.71 — Reference guides and palette flow

A native-resolution, non-destructive reference image is pinned to the bottom of the Layers panel. Its original pixels remain in editable project data and can be moved, scaled, rotated, hidden and faded without repeated raster resampling. References remain visible as guides but are not included in PNG exports or published images. Palette Flow optionally bounces backward at the last swatch; select any swatch and use Edit swatch to change its colour and the resulting gradients. Public Open link is styled like Copy link and opens a new tab.


## v0.1.72 — Independent palette gradients

Selecting a palette swatch changes the active brush pigment without overwriting the first custom-colour swatch. Editing a palette swatch updates only that swatch; Gradients now blend from the first to the final swatch, preserving edited endpoints. Palette colours and the active brush colour are stored independently.

## v0.1.73 — Reference uses normal layer transforms

In **Layers**, add a reference guide and select its bottom-pinned thumbnail row just as you would a painting layer. Use the existing **Move**, **Rotate** and **Scale** controls (desktop **G**, **R**, **S**, or mobile layer-transform controls) to transform the guide. Cancel or apply using the normal tool workflow. Reference thumbnails, visibility and opacity are in the normal Layers list rather than a separate adjustment panel. The source image remains at its original resolution and is excluded from rendered PNG exports and public publication. References persist in editable project records; painting layers are not merged with or overwritten by the reference.

### Contextual Rantlist discussion (v0.1.75)

Public viewer **Discuss art** follows the displayed publication, sending its token in an opt-in Rantlist share-intent URL while retaining the viewer in its original tab. The Rantlist side needs a receiver to display an authenticated #lobby composer with a native medium image attachment. Until deployed, the current painting URL is offered for manual sharing; no message is posted just by opening the link.

## Rantlist discussion handoff (v0.1.76)

The Publish actions and public gallery viewer now use the same artwork-specific Rantlist #lobby link. Opening Rantlist does not itself send a message; the native image draft depends on a separately installed Rantlist share-intent receiver. See `app/docs/RANTLIST_DISCUSS_ART_ACTION_v3.md`.

## v0.1.78: Custom gradients and public gallery identity

The Colour palette now has clearly checked Flow and Bounce pill switches. Save named live multistop gradients directly in Custom gradients, reopen them with normalized anchor positions across XL/M/S, and delete saved presets with confirmation. These presets remain local to the browser; they do not publish artwork or synchronize with an account. The public gallery and viewer use the editor’s pastel Paint-lab text logo for the Paint Lab home link.
