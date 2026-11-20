# Paint Lab — Development Changelog

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

