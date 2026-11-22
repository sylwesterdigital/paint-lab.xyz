# v0.1.38 — Git Worktree Archive Preflight Repair (2026-11-22)

- Prevent safe, untracked `PAINT_LAB_RELEASE_vX.Y.Z.zip` artifacts at the Git repository root from failing the deployment preflight. Only regular files matching the exact versioned archive pattern are ignored; arbitrary untracked files and modified tracked files still block the release.
- Apply the same exception to the GitHub README/ABOUT/CHANGELOG sync gate, and bump the bundled watcher to v0.1.6.
- Add tests for benign release artifacts versus unrelated untracked files, modified tracked files and symlinks. Keep Git/SSH/manifest/Ubuntu layout validation intact.
- Retain the v0.1.37 account save and public share compatibility changes. An existing v0.1.5 watcher still needs the obstructing root ZIP moved under `updates/archive/` before it can deploy the upgraded watcher.

# v0.1.37 — Account Save & Public Share Format Compatibility (2026-11-21)

- Fix the confirmed incompatible API: browser `paint-lab-webgl` document version 4 is now accepted by Flask project create, retrieve and overwrite. Legacy versions 2/3 remain supported. No SQLite migration or loss of existing projects.
- Add an independently testable backend validator to keep browser project actions, layer filters, reveal strokes and server JSON persistence compatible. Preserve action data verbatim rather than migrating or downgrading it.
- Keep public links as **PNG-only images**, separate from private editable cloud canvases. Validate PNG chunk structure, CRC checksums and dimensions before writing public files.
- Automatically reduce public PNG dimensions if highly detailed artworks exceed the server's 7 MB public-image ceiling; local device sharing keeps full resolution. Account saves now give a clear 16 MB editable-history limit error.
- Verify project JSON round trips through SQLite, v2-v4 compatibility, and malformed publication rejection in mandatory non-Flask tests; the Flask endpoint integration suite runs on the Ubuntu server.

# v0.1.36 — Existing-Image Mask Reveal Filters (2026-11-21)

- Stylization is now a **reveal brush for existing artwork**. The brush provides an alpha mask; the pixels beneath it are sampled and converted to Pixel, Halftone, ASCII, Mosaic, Symbols or another composite effect. No new pigment is applied.
- The brush uses a snapshot of the visible canvas (including underlying layers) at stroke start. Blank canvas generates no new marks.
- Filter cells are anchored to document coordinates, and results are clipped by both existing image transparency and the pressure-sensitive stroke mask.
- Preserve live reveal preview, deterministic undo/redo and saved-project replay. The earlier stroke-fx-v2 and legacy layer-filter behaviours remain available for existing saved histories.
- Ship with a manifest, SHA-256 checksums and app-only Ubuntu installation preflight; production is not deployed by the build.

# v0.1.35 — Painted-Stroke Image Filters (2026-11-21)

- New stroke stylization transforms the RGBA output of an ordinarily painted brush stroke. The original selected oil, watercolour, chalk or pencil instrument renders first, then its image is transformed into Pixel, Halftone, ASCII, Symbols, Mosaic or another filter.
- The new filtered stroke can be previewed while drawing and is composited to its target layer at release. Existing pixels and other layers are not passed through the filter.
- Choosing a filter no longer applies it immediately to an entire existing layer. The old layer-filter actions remain available for imported older-project replay.
- Store stroke effect and pattern parameters on new stroke actions to retain undo/redo, deterministic replay and editable-project portability.
- Keep the manifest-based release packaging and existing macOS watcher/Ubuntu rollout safeguards.

# v0.1.34 — Immediate Pixel Filters (2026-11-21)

- Fix the Stylize panel showing Pixel selected while the active layer still had zero filters: tapping a filter now immediately applies it to existing active-layer pixels, and selecting another filter builds a composite stack. None clears the stack.
- Make the active style highlight reflect the actual applied layer-filter stack, not a previously saved un-applied preset. Show an applied filter count and edit the topmost effect without changing painting tools.
- Rebuild Pixel as a true image-space block effect with colour and transparency sampled from the already-painted layer, distinct from oil-brush bristle marks. Increase pixel cell size control to 96 pixels and default to 24 pixels for a visible result.
- Treat filter intensity as a blend between the original layer pixels and the filtered image instead of reducing paint opacity. Update size and intensity immediately during slider drags and commit one undoable action when the slider is released.
- Keep non-destructive layer filters, composited export, portable editable project support, legacy stroke replay, production watcher, release manifest and SHA-256 checks.

- Separate the new layer-filter selection from painting-engine routing: Pixel, Halftone and Invert no longer divert oil-brush or pencil strokes into the old stamp renderer. Preserve the previous renderer for legacy stylized strokes.

# v0.1.33 — Composite Layer Stylization (2026-11-21)

- Redesign stylization as a **composite layer filter system**. Halftone, ASCII, symbols, pixelate, mosaic and invert now transform the existing painted pixels on the active layer instead of behaving like a spray or stamp brush.
- Add a **non-destructive active-layer filter stack** with Add, Replace, Remove last and Clear controls, enabling several composite filters to be combined on the same layer.
- Apply filtered appearance consistently in the live composite, layer thumbnails, export, merge and portable-project import/export paths.
- Preserve backward compatibility for older projects that saved stamp-style stroke stylization; those legacy strokes still replay through the old renderer, while new work uses the layer-based model.
- Keep the v0.1.32 oil-contact and packaging safeguards intact.

# v0.1.32 — Production Test Layout Repair (2026-11-21)

- Fix the Ubuntu deployment blocker introduced in v0.1.30: the release-integrity regression no longer assumes the macOS watcher exists beside the installed application. The test validates both the packaged source tree and the actual app-only Ubuntu release layout without masking failures.
- Upgrade the packaged release watcher to v0.1.5 and run the complete Python suite a second time in an isolated releases/vX.Y.Z directory containing only app/ files, matching what install.py actually deploys. Reject incompatible releases before SSH deployment.
- Keep the existing canonical development-log validation, version-matched offline UI, SHA-256 manifest, Python/JavaScript checks, preflight gates, staged deployment and rollback safeguards.
- Retain v0.1.30 oil-brush sparse-sample interpolation, bounded high-DPI endpoint rendering and legacy editable-stroke replay compatibility. This release repairs packaging and deployment validation; it does not introduce a new paint solver.
- Preserve the complete development history, including v0.1.30 and v0.1.29, and add regression coverage for version markers, embedded notes and the production-specific test layout.

# v0.1.30 — Release Log Integrity & UI Reliability (2026-11-21)

- Correct the v0.1.26 What’s New dialog in later releases by embedding the complete current changelog from one canonical source; display v0.1.30 instantly while preserving previous releases for offline viewing.
- Fetch release notes only for the running app version; validate project, version, title and history, preserve the selected tab, and stop stale asynchronous results from replacing newer dialogs.
- Add deterministic history generation plus strict validation in the ZIP builder and watcher v0.1.4; reject packages whose embedded, canonical and public release logs disagree before production deployment.
- Repair oil-paint continuity after sparse stylus samples and large pointer jumps: adaptively subdivide travel with interpolated pressure and timestamps rather than dropping oversized patches or spacing 120 dabs too far apart.
- Shape larger high-DPI oil touchdown/lift-off footprints using bounded 256×256 pixel tiles rather than silently skipping the entire endpoint when its bounding rectangle exceeds the old 850,000-pixel limit.
- Version the adaptive oil-sampling engine per new stroke so already-saved projects retain the legacy replay path. Keep painting, layer and project formats compatible.
- Add Chromium pixel regressions for round, flat and rigger sparse oil strokes at 1× and 1.5× DPR, plus versioned-log dialog tests covering offline, stale network data, reopen and once-per-release behaviour.
- Continue to distinguish the 2D raster oil approximation from the future GPU pigment, wetness and paint-height architecture. No GPU fluid or height-field solver is claimed in this release.

# v0.1.29 — Oil Brush Touchdown and Lift-off (2026-11-21)

- Correct oil brush touchdown and lift-off together with tip-family-specific contact envelopes: strokes expand from a narrow initial contact and narrow again without separated disc caps or rectangular cutoffs.
- Derive start response from recorded initial pressure and acceleration; derive release from deceleration and final pressure, retaining distinct flat, fan, round, and liner endpoints.
- Limit taper regions on short strokes, preserve underlying pigment when reducing the deposited footprint, and keep pixel readbacks bounded for touch devices.
- Study user-provided Brushwork VR shader architecture: brush contact depth, separate load and pickup textures, pigment deposition and canvas-height shading; document the larger GPU renderer requirements without claiming a fluid solver.
- Run Chromium alpha-profile, short-stroke connectivity, pen-pressure and brush-family rendering checks; verify the deployment ZIP manifest and hashes.
- Speed up release validation by compiling all Python files in one subprocess; watcher v0.1.3 retains SHA-256 manifest checks and the same deployment gates.

# v0.1.28 — Continuous Pencil Rendering (2026-11-21)

- Pencil strokes now follow continuous quadratic paths with round joins instead of placing spaced pigment stamps.
- Pencil size maps to a narrow lead contact; hardness adjusts edge softness and pigment density, with limited pressure dynamics.
- Color remains the selected pencil hue; palette colour travel continues to work.
- Legacy drawing history retains its original rendering path; new Pencil strokes save the new engine version.
- Browser tests cover long and sparse point paths, uninterrupted opacity and chosen colour.

# v0.1.27 — Velocity-Sensitive Oil Brush Lift (2026-11-21)

- Replace the detached circular cap and the uniform clipped end with a curved-path brush lift tied to recorded velocity and stylus pressure.
- Slow releases form a longer narrowing tail; quick movement releases more abruptly, without adding a half-disc.
- Apply tip-specific release profiles: pointed/liner, round/filbert/mop, flat/chisel, and separated comb/rake/fan deposits.
- Preserve original underpainting and active bristle relief using bounded, deterministic endpoint processing. This remains a 2D wet-paint approximation, not a full GPU fluid solver.

# v0.1.26 — Reliable Mobile Touch & Oil Brush Ends (2026-11-21)

- Prevent mobile canvas gestures from retaining stale touch IDs after pointer cancellation, lost capture, backgrounding, or window blur; require two live contacts for pinch and rotation.
- Block remaining fingers from painting or rotating after a multi-touch gesture until all fingers have lifted, then restore immediate single-contact drawing.
- Use a short provisional touch grace period and per-stroke pixel rollback tiles so a late second finger cancels accidental paint without replaying the full project history.
- Selecting a pigment or brush tip now exits any leftover layer-transform state so drawing cannot accidentally manipulate a layer pivot.
- Make the chosen palette swatch and brush tip visibly selected, with contrast-safe insets, checkmarks, and aria-pressed states.
- Replace zero-length oil bristle fanning, damp sudden tip-angle changes, and round solid-tip stroke endpoints without flattening the interior bristle relief; preserve separated comb, rake and fan endings.
- Add targeted regression tests for gesture lock release, touch rollback, oil stroke finish and active UI selection.

# v0.1.25 — Smear, Smudge, Blend & Effect Mode Repair (2026-11-21)

- Fix Smear, Smudge, and Blend to act on existing painted pixels, rather than drawing more paint. Each uses a different retouch sampling algorithm and supports colour beneath a transparent active layer.
- Returning to Paint or selecting Pencil, Chalk, Watercolour, or Oil resets retouch mode.
- Eliminate initial retouch marks before the pointer moves.
- Fix repeated stylization readback warnings; move keyboard focus out of the closing Studio Settings drawer before applying aria-hidden.

# v0.1.24 — Server Test Dependency Fix (2026-11-21)

- Repair Ubuntu release validation: the public-sharing integration test generated its PNG with Pillow although Pillow was not a declared runtime dependency.
- Build the same fully valid 4×4 PNG using only Python `struct` and `zlib`, so all server-side sharing and revocation tests still execute.
- Exclude local pytest/mypy/ruff caches from release manifests. No application features or persistence formats are changed.

# v0.1.23 — Portable Artworks, Canvas Presets & Sharing (2026-11-21)

- New Canvas presets and custom pixel dimensions, optional artwork naming.
- ZIP project export/import with editable history, layer PNGs, brush assets and preview.
- Save-dialog PNG shortcuts and Web Share image support.
- Opt-in public image publishing with private-account ownership, revocation and public gallery.

# v0.1.22 — Pointer-anchored desktop transforms and verified releases (2026-11-21)

- Make desktop G, R, S, and Shift+D transforms confirm with a single left click (Enter also confirms), and cancel with right-click or Escape without a click-and-drag.
- Anchor the transform to the last desktop mouse position in canvas document coordinates; preserve the original grab offset at arbitrary zoom and canvas rotation instead of jumping to the layer-centre pivot.
- If no mouse position is available when the keyboard shortcut is pressed, establish it on first movement without displacing the artwork.
- Correct the release process: build the ZIP through tools/build_release.py to include the required manifest.json, SHA256 checksums, and bundled watcher for the existing deployment pipeline.
- Retain v0.1.21 pencil, text-brush and appearance controls and restore historical development-log entries.

# v0.1.21 — Live Chrome Preview, Truer Pencil & Character Brush (2026-11-21)

- Clear Canvas now removes the old layer stack and starts with exactly one transparent Background paint layer; Undo restores the complete previous multi-layer composition and Redo clears again.
- Keep earlier projects compatible: historical Clear actions retain their original layer-preserving meaning; new resets carry an explicit resetLayers history marker.
- Speed up reconstruction of a cleared drawing by skipping all strokes and layer changes before the latest full reset while keeping the editable Undo history.
- Correct oil-paint contamination: cache the original paint beneath each stroke in bounded tiles, so a brush never picks up its own shaded relief pixels as dark pigment.
- Limit wet-colour uptake and separate surface lighting from pigment mixing so white and pale oil remain clean on unpainted canvas while still mixing with genuine existing paint.
- Add browser and regression checks for layer reset, undo/redo, saved-project recovery and white oil strokes.

# v0.1.19 — Recovery Safety & Fast Resume (2026-11-21)

- Fix stale recovery replay painting over a cleared or replaced canvas. Clear, New, Undo and project switching invalidate in-flight restoration before pixels can be applied.
- Cache full-fidelity layer pixel snapshots alongside matching IndexedDB recovery history, so subsequent restarts restore the current image without replaying hundreds of strokes.
- Use cancellable, responsive legacy-history replay with a Stop restoring control. Preserve a recovery backup in Gallery before skipping a long restore.
- Skip paint actions made before the most recent Clear during rebuilding, without discarding history needed for Undo or saved projects.
- Throttle startup console progress logs, and fix cropping of the animated Paint Lab title.

# v0.1.18 — Denser Oil Pigment & Startup Polish (2026-11-21)

- Make loaded oil brushes lay down a contiguous, substantially more opaque paint body rather than evenly spaced semi-transparent strands; preserve intentionally separated rake, comb and stipple tips.
- Improve bristle spacing and stroke sampling while retaining directional ridge highlights, per-strand colour pickup and paint-load controls.
- Show the deployed version directly in the browser tab title.
- Display a brief pastel-gradient Paint Lab title after release notes are dismissed, or on refresh when notes have already been read; the animation never blocks painting.
- Open Save New with an empty name field and save an unnamed artwork as Untitled.

# v0.1.17 — Multi-select & Merge Layers (2026-11-21)

- Select layers like Finder: Shift-click for a continuous range and Command/Ctrl-click for non-adjacent layers; thumbnails also support modified selection without losing drag-to-reorder.
- Duplicate, delete, and toggle visibility for multiple selected layers in a single undoable history step.
- Merge selected layers or all layers into a single raster layer at document pixel resolution, retaining visible opacity and blend results; confirm hidden and non-adjacent merge caveats before proceeding.
- Show the supplied closed-eye SVG when a layer is hidden, and the existing eye icon when visible.
- Preserve grouped layer actions through editable project JSON, autosave, redo/undo, and release notes.

# v0.1.16 — Reliable Brush Tips & Server Diagnostics (2026-11-21)

- Fix oil brush-tip fidelity: round, liner, flat, fan, rake, mop, sword and imported brush shapes now drive actual bristle contacts and stroke widths instead of identical uniform oil ribbons.
- Make development release notes display immediately from packaged data; fetch the server changelog in the background with a short timeout.
- Restore recent browser artwork incrementally with progress and no redundant full synchronous replay; expose client startup timings.
- Add an authenticated administrator-only application log terminal with adjustable font size, pause/resume, refresh and copy; log request duration and errors without request bodies or provider secrets.
- Add a server-shell administrator-provisioning CLI and backwards-compatible SQLite user role migration, without any default administrator passwords.

# v0.1.15 — Adjustable Window Chrome & Natural Stroke Widening (2026-11-21)

- Adjustable border visibility, window opacity, shadows, shadow strength and backdrop blur in Settings → Appearance.
- Natural-width controls under Brush & Paint → Dynamics: enable/disable, initial tip width, travel before full width and speed reduction.
- Reproducible per-stroke widening in oil and non-oil brushes; saved in editable history and settings presets.

# Paint Lab — Changelog

## v0.1.14 — Stylized brushes, wet-pigment oil and shared brush atlas (2026-11-21)

- Separate stroke effects: halftone, ASCII, invert, pixelate, mosaic and symbol stamping, independently adjustable from pencil/chalk/watercolour/oil.
- Replaced freehand oil stamp repetition with a persistent multi-bristle paint-load model, wet underlying pigment pickup, subtractive-reflectance mixing and local pressure/viscosity-dependent deposition and simulated ridge shading.
- Reduced Brush Tips from 24 separate thumbnail canvases to a single cached image atlas; custom brush imports cause one atlas rebuild. Reuse inversion-mask buffers to avoid allocations per dab.
- Styles are saved with strokes, with editable-history undo/redo and gallery JSON replay preserved.
- The oil engine is a lightweight interactive wet-pigment approximation. It **does not** contain the full GPU fluid simulation of [David Li — Fluid Paint](https://github.com/dli/paint) (MIT). [Patch — Oil Paint](https://patch.gg/blendi/oil-paint) (MIT/CC0) is a reference for sculptural dabs and directional marks, not a physical paint solver.

## v0.1.13 — Distinct pigment texture engines (2026-11-21)

- Pencil: narrow irregular graphite marks and paper grain rather than full-width opaque paint.
- Chalk: granular, fragmented deposits with visible dry-paper gaps and powder crumbs.
- Watercolour: translucent wash, diffused edges, bloom backruns and pooled pigment.
- Oil: opaque, full-bodied strokes with directional bristle grooves, bright ridges and darker valleys.
- Material-specific stamp textures are cached for live performance, with deterministic stroke replay and preserved brush-tip shapes.

## v0.1.12 — Immediate Desktop Transforms & Shift+D (2026-11-21)

- `G`, `R`, `S`: instantly follow desktop mouse movement after pressing the shortcut (no held mouse button).
- `Shift + D`: provisionally duplicate the active layer or selected shape and move the new copy with the mouse.
- Left-click or Enter confirms; Esc or right-click cancels without adding an operation.
- Preserve layer zoom invariance, save/reopen, and one-step Undo/Redo for duplicate-and-move.

## v0.1.11 — Mobile navigation performance and contextual transforms (2026-11-20)

- Fix mobile pinch/pan/rotation freezing by separating the static document paint texture from viewport transforms; gestures no longer recompose every layer or reupload the painted texture.
- Reduce gesture-frame shader work and skip unnecessary palette DOM reconstruction, brush-preview updates and selection redraw during navigation; restore full-quality paper when navigation ends.
- Do not replay the entire painting history when a second finger starts a gesture during a stroke; commit the in-progress stroke safely.
- Hide the mobile Move/Rotate/Scale buttons outside an active transform. Activate transforms through the Layers tool sheet, then use the contextual right-side controls.
- Retain independent two-finger canvas navigation when no artwork transform is selected, and keep existing desktop shortcuts, project data and layers intact.


## v0.1.10 — View-safe transforms & mobile canvas rotation (2026-11-20)

- Fix layer duplication scaling at zoom levels other than 100% and on high-DPI displays by copying the native pixel buffer without an inherited DPR transform.
- Add document-coordinate Move (G), Rotate (R) and Scale (S) manipulation to the active layer; transformations use a live preview and join Undo/Redo and editable project history.
- Apply the same move, rotation and scale gestures to a selected vector shape instead of the entire layer.
- Expose three compact, independent mobile transform buttons on the right side, and route two-finger rotate/pinch/pan gestures to the object only when a transform mode is selected.
- Restore canvas rotation as a default mobile gesture, migrate previous disabled defaults once, and accumulate angular changes without wraparound jumps.
- Keep normal two-finger canvas zoom, pan and rotation isolated from layer transforms and provide Escape to leave transform modes.


## v0.1.9 — Mobile brush controls and stable gestures (2026-11-20)

- Place Undo/Redo in the bottom-right corner of mobile painting, shown by default with disabled states.
- Show the currently selected brush-tip silhouette above the colour swatch and in the brush-size control.
- Replace the native vertical range input with a draggable touch slider, a larger thumb, and a live size value.
- Stabilize multi-touch zoom using stable touch pairing and canvas-local positions; optional deliberate rotation, off by default on mobile.
- Provide an accessible Account/Profile entry and Fit and straighten canvas action in mobile settings.


## v0.1.8 — Safe, undoable canvas clearing (2026-11-20)

- Add a trash-can action to the desktop toolbar, mobile painting controls and History panel.
- Use a custom three-choice dialog: No, Yes—clear, or Save before clearing; never a browser-native confirmation.
- Save before clearing creates a named copy in the local gallery and clears only after its IndexedDB write succeeds; cancellation or failure leaves the artwork intact.
- Clear paint from every layer while keeping layer structure, paper and canvas dimensions; Undo and Redo restore the operation.
- Make Clear canvas optionally visible on the mobile toolbar, enabled by default, while retaining the paint-only focus mode.

## v0.1.7 — Mobile canvas-first studio (2026-11-20)

- Introduce a dedicated mobile painting workspace with an edge-to-edge canvas and one-tap focus mode that hides every control except the upper-left toggle.
- Add a minimal bottom-left colour swatch with an edge-anchored scrolling palette, palette-cycle control and native custom-colour picker.
- Add compact brush-tip cycling, a vertical diameter slider, pigment cycling and optional eraser, undo and painting status controls.
- Move mobile canvas preferences and access to the full brush, effects, shapes, layers, paper, gallery and export tools into a touch-friendly Settings drawer and tool sheets.
- Remember mobile control visibility and focus preferences independently from the desktop floating-panel workspace.

## v0.1.6 — Document view and compact brush workspace (2026-11-20)

- Immediate zoom/pan/rotation redraw, independent of brush strokes.
- Paper document edges with neutral checkerboard surrounding the artwork.
- Compact panel headers with interactive colour swatches when Palette is collapsed.
- Adaptive brush-tip gallery density to show more tips at useful sizes.
- Correct cloud login and AI API-key field form associations.

# Paint Lab changelog

[Paint Lab](https://paint-lab.xyz/) · [GitHub](https://github.com/sylwesterdigital/paint-lab.xyz) · [Project story](ABOUT.md)

The in-app **What’s New** overlay is sourced from `app/frontend/changelog.json`. Earlier versions are retained in its History tab.

## v0.1.5 — Adaptive Palette & Colour Transformations

Released: 2026-11-20

- Replace the redundant 25th palette tile with the native colour picker as the first of 24 swatches, eliminating the orphan final row.
- Automatically reflow the entire colour grid to complete rows as the floating palette is resized, including very wide, short layouts.
- Make Gradients blend the selected first colour through optional Shift-selected stops to the final swatch using perceptual OKLab interpolation.
- Make Pastels, Sharp, Chromatics and Sepias transform existing colours rather than replace the palette; add Warm, Cool, Earth, Neon, Muted, Vintage, Monochrome and Invert modifiers.
- Use the supplied distinct SVG designs for Fit panel and Collapse panel controls.

## v0.1.4 — What’s New & Development Log

Released: 2026-11-20

- Add a What’s New overlay after each new release, with a Latest tab and searchable-by-version history list.
- Remember which release notes were dismissed on each browser, and reopen them any time from the toolbar.
- Publish the same release history to the public application and the GitHub repository.
- Add project README, ABOUT and CHANGELOG documents with development, deployment, API and future roadmap context.
- Extend the ZIP watcher with verified, guarded synchronization of GitHub-root documentation.

## v0.1.3 — Fast painting workflow and reusable brush tips

Released: 2026-11-20

- One-tap Pencil, Chalk, Watercolour and Oil on the draggable tool rail, plus an always-visible painting status strip.
- Compact colour-first palette, procedural and imported image brush tips, and brush tip categories.
- Faster layer add, clone, delete and reorder; paged stroke history without losing editable actions.

## v0.1.2 — SVG icon library and desktop shortcuts

Released: 2026-11-20

- Replace many text-based action symbols with theme-aware SVG icons supplied for the application.
- Fix Command+/ and Ctrl+/ to display the keyboard shortcuts help overlay.

## v0.1.1 — Coloured watcher and safer TLS bootstrap

Released: 2026-11-20

- Improve watcher output with distinct coloured deployment start, success, warning and failure banners.
- Reuse existing Let’s Encrypt Certbot accounts where available when issuing the Paint Lab certificate.

## v0.1.0 — First versioned Paint Lab service

Released: 2026-11-20

- Package the browser painting studio with brush materials, procedural tips, canvas layers and IndexedDB gallery.
- Add Flask, authenticated SQLite canvases, WebSocket notifications and an encrypted AI API-key vault.
- Introduce an isolated Ubuntu nginx/systemd deployment and SHA-256 verified ZIP release watcher.

