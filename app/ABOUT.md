# About Paint Lab

[Paint Lab](https://paint-lab.xyz/) · [GitHub](https://github.com/sylwesterdigital/paint-lab.xyz) · [Development log](CHANGELOG.md) · [Report an issue](https://github.com/sylwesterdigital/paint-lab.xyz/issues)

## A creative workspace that stays out of the way

Paint Lab explores a simple idea: a creative application should let artists move quickly between making marks, choosing material, mixing colours, shaping geometry and organising a canvas—without burying essential tools behind a configuration drawer.

Its interface is designed around a full-window canvas, a small draggable quick-tool stack, focused floating panels and a compact live status display. Painting materials (pencil, chalk, watercolour, oil) are independent from brush shapes and from actions such as erasing, blending and smudging. Tools and canvas view remain separate, so zooming and rotating artwork doesn't resize the interface.

## What exists today

The editor includes programmable/procedural tips, imported brush masks, adjustable flow and pigment, shape tools, layer visibility/order/opacity/blend modes, colour palette presets and generators, image-based colour extraction, paper surfaces, undo/redo and export. The palette reflows as its window is resized, and colour modifiers operate on the existing colours; multistop gradients are generated between chosen colours. It supports mouse, touch, stylus pressure where browsers expose it, and canvas-only gestures. Workspace preferences and unsaved drafts are remembered locally when browser storage permits.

Authenticated Flask/SQLite storage is optional: the editor can retain browser-local art independently. Server features provide private saved canvases and notifications over WebSockets, plus an encrypted per-user vault to store provider API keys and verify connectivity. **There is no AI-driven painting, model inference for layers or social sharing/chat integration in this release.** The vault is groundwork, not an active AI feature.

## Why versioned releases

Paint Lab's app version, public development log and GitHub changelog are derived from one release record. Each packaged update includes regression tests and SHA-256 manifest checks. A local release watcher validates the ZIP, checks Git and remote preconditions, stages and verifies the server install, then publishes the source and repository documentation. Other sites, certificates, databases and services are deliberately isolated.

## Planned directions (not yet implemented)

- AI-assisted, opt-in operations on selected layers or regions, with explicit permission and preview.
- Canvas-sharing across collaboration, chat and spatial/multiverse experiences.
- Better physical pigment and brush simulation, deeper tilt/rotation response and device performance work.
- Multi-user workflows, revisions, permissions and backup/recovery tooling appropriate to production accounts.

## Related work and community

Paint Lab shares an interest in natural interaction and user agency with [FREE-LAB.cam](https://free-lab.cam/), a separate WebXR experiment. Watch [the FREE-LAB short film on YouTube](https://youtu.be/rJ0nFm7jKms) for that project's context, not for a Paint Lab product preview.

For Paint Lab source, feedback and collaboration, use [the GitHub repository](https://github.com/sylwesterdigital/paint-lab.xyz) or [its issue tracker](https://github.com/sylwesterdigital/paint-lab.xyz/issues). No official Paint Lab accounts on other social networks have been provided or verified.


## Mobile painting (v0.1.7)

Paint Lab provides a canvas-first mobile experience with a single show/hide control, edge-anchored colour picker, direct brush size and pigment controls, and optional tool sheets for deeper editing. The floating desktop workspace remains unchanged.


### Safe clearing

Paint Lab v0.1.8 adds a trash-can action on desktop and mobile. Clearing opens a three-choice dialog (cancel, clear, or save a named gallery copy before clearing). The operation preserves canvas dimensions, paper and layers, remains undoable, and does not delete the project history.


### Touch and accessibility

The mobile studio separates painting from settings and avoids desktop-style floating windows. Current touch controls include a custom brush-size slider, contextual brush-tip preview, bottom-right Undo/Redo, and deliberately opt-in canvas rotation.

## Layer and shape manipulation

Painting layers can be moved, rotated or scaled using **G/R/S** on desktop. Mobile users can choose right-edge Move, Rotate or Scale tools; two fingers transform the object only in a transform mode. Otherwise pinch, twist and pan navigate the canvas. Changes are undoable and are saved with the editable project.

## Pigment rendering

Paint Lab models four distinct digital mark-making behaviours: graphite grain, pastel/chalk deposits, pigment washes and opaque bristle-structured oil paint. These are procedural screen-space approximations rather than physically accurate wet-media fluid or three-dimensional impasto simulations.

### Stroke-masked image reveal filters (v0.1.36)

In Brush & Paint → **Stylize**, choose Pixel, Halftone, ASCII, Symbols, Mosaic, Invert or another conversion filter, then brush over **already-existing artwork**. The brush pressure and tip determine a reveal mask; the filter reads the *existing visible image* under the mask, not newly deposited pigment. A transparent empty area stays empty. New stroke actions record `existing-image-fx-v3` for replay and undo/redo, while pre-0.1.36 saved stylization actions retain their historical appearance. Filter patterns stay aligned to document coordinates. The brush engine remains a 2D raster approximation, not a GPU pigment solver.

### Stroke stylization (v0.1.14)

Brush & Paint → **Stylize** offers halftone, ASCII, inverted-colour, pixel, mosaic and symbol strokes. The stroke effect is separate from Pencil/Chalk/Watercolour/Oil and the artistic tip. Pattern size and strength are configurable and saved with each stroke. Oil freehand now uses a persistent bristle-load contact model: bristles pick up underlying colour, deposit mixed pigment and draw thickness-dependent ridges. The 24 Brush Tips thumbnails share a single cached atlas, rather than using 24 canvases. This is a bounded wet-media 2D approximation, not the full GPU fluid solver. References: [David Li Fluid Paint](https://github.com/dli/paint) (MIT), [Patch Oil Paint](https://patch.gg/blendi/oil-paint) (MIT/CC0).


### v0.1.15 — Workspace appearance and natural brush dynamics

In Studio Settings → Appearance, adjust floating-window borders, transparency, shadows and backdrop blur. In Brush & Paint → Dynamics, enable natural stroke widening and adjust the initial tip contact, growth distance and speed response. Controls persist with workspace presets and individual brush strokes.

## Brush geometry and operational visibility (v0.1.16)

Brush tips now govern the bristle contacts in the wet-oil stroke renderer, making marks from round, liner, fan, rake, flat and custom image tips genuinely different. This remains an experimental 2-D pigment model, not a physical Navier–Stokes paint simulation. Startup and autosave recovery are more visible, and server operators can inspect application-level errors and request times through a role-protected console without exposing credentials or unrestricted machine logs.

## Multi-layer editing (v0.1.17)

Layer selection supports Shift for a continuous range and Command/Ctrl for non-adjacent layers. Selected layers can be duplicated, hidden, removed or merged together. A merge creates a new raster layer; hidden sources contribute no visible pigment, and merging non-adjacent layers can alter stacking interactions with unselected layers. Undo restores the original layers.

## Recovery and safety

The local gallery uses IndexedDB. v0.1.20 saves painted layer pixel snapshots beside editable history to enable fast startup. A long legacy recovery can be stopped, backed up, and restarted from Gallery. Clearing a drawing cancels in-progress recovery and cannot be overwritten by stale replay.

## Canvas clearing and oil colour

Clear Canvas in v0.1.20 starts one empty layer, while retaining the full editable Undo history; previous projects remain compatible. Oil-paint strokes keep a bounded, pre-stroke underpainting sample so shaded pigment highlights never feed their own darkness back into a loaded brush.


## v0.1.23 desktop transforms & release validation

Keyboard transforms use the desktop pointer position without snapping the layer to its centre. Left-click or Enter confirms; right-click or Escape cancels. Verified releases are built with `python3 app/tools/build_release.py` to include a SHA-256 manifest and watcher.

## v0.1.23 — Portable canvases and public artwork

Creating a new canvas now offers common aspect ratios, viewport fit, and custom pixel dimensions up to 16 megapixels; a new optional name becomes the Save Artwork default. Local exports include PNG with or without paper and a portable `.paintlab.zip` file carrying `project.json`, PNG layer assets, imported brush tips, and a preview. The project history remains editable after ZIP import. ZIP files use stored entries (each PNG is already compressed internally), making them readable by general ZIP tools without an online library.

Sharing is explicitly separate from private cloud canvases. A PNG may be shared through the operating system's Web Share sheet, falling back to download when unavailable. Signed-in users can choose to publish a rendered PNG, obtain a revocable public link, and maintain a public image gallery at `/u/<username>`. Everyone may browse `/explore`, an opt-in-only global public artwork feed with search and date sorting. Rantlist.me is linked as an external conversation venue, with no automated transfer of artwork or user data. Public visitors cannot read private editable history or provider credentials.

### Palette sizes and movement-driven colour flow (v0.1.23)

The Palette header supports **XL** (8 large swatches), **M** (24), and **S** (48 smaller swatches). Switching size retains the underlying palette; extra small swatches are generated by perceptual interpolation. The **Flow** switch, next to the harmony generator, advances brush pigment through the selected palette only as the pointer travels. The selection and sampled colours are captured per stroke for deterministic Undo/Redo and reopening; the setting is also stored in workspace presets.

Paint Lab v0.1.25: Smear, Smudge, and Blend operate on source pixels, and the Paint tab exits retouch mode.


## Mobile touch and painting (v0.1.26)

Multi-touch gestures exclusively pan, pinch, and rotate the canvas while two fingers are down. The remaining finger stays navigation-only until all contacts are released. Oil brushes now start and end without the artificial bristle-fan star; active swatches and tips have strong selection markers.

Paint Lab v0.1.27 improves physically motivated oil-brush lift and release behaviour based on pen pressure and motion deceleration. It is a bounded 2D wet-pigment model, not yet a GPU fluid/paint-thickness simulation.

Paint Lab v0.1.28 uses a dedicated, continuous Pencil drawing path distinct from stamp-based brushes. New history actions save an explicit pencil engine version so old projects are not silently altered.

### Oil contact progression (v0.1.29)

The current 2D oil engine now shapes initial contact and lift-off according to brush family and pointer motion, avoiding synthetic endpoint discs. A staged path toward independent pigment/wetness/height buffers is documented in [Painting simulation research](docs/PAINT_SIMULATION_RESEARCH.md). Brushwork VR is used as a technical reference; this release does not import its code or implement its GPU paint-height solver.

## Release-history reliability (v0.1.30)

The version displayed in What's New now comes from the packaged version-matched release history, with a verified same-version network refresh. The release build and deployment watcher reject stale embedded notes and unequal changelog copies. The same release fixes missing pigment after sparse oil-stylus samples and shapes high-DPI endpoints in bounded tiles. Existing saved strokes remain on their legacy rendering path. This release does not introduce a GPU-based paint solver.

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

Save & share now offers **Save & Publish**, which creates a new editable local gallery copy and then publishes the visible PNG with a single click; this never silently overwrites an existing saved artwork. After publishing, **Open link** opens the public artwork alongside Copy link. **Share to Rantlist #lobby** is opt-in. Until Rantlist deploys its authenticated bot receiver it copies the publication URL and opens Rantlist for manual posting; it never claims the chat message was sent. The separate signed server-to-server bot bridge is fully specified in [Rantlist integration](docs/RANTLIST_INTEGRATION.md) and disabled until server secrets are configured. No private project history or login data is shared.
