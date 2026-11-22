# Paint Lab analytics and responsive history (v0.1.63)

## Analytics

The Paint Lab studio and public artwork/gallery pages load the Umami tracker from
`https://analytics.mielniczuk.com/script.js` with website ID
`bd5f9b1c-f457-47a5-81e6-e7bbe57bca9d`. The tracker is injected with
`async` after the page loads, during browser idle time, and the application
never waits for its success. Offline or blocked tracking has no impact on drawing.

A bounded set of coarse events is recorded: local/cloud saves, public
publication, artwork export/opening, gallery opening, and occasional changes to
painting mode, effect or stylization. A maximum of 40 custom events is sent in
one page session. No artwork, canvas pixels, titles, usernames, credentials,
brush point data or project history are included in custom event payloads.
Standard Umami pageview tracking is left enabled. Analytics can be disabled by
blocking the tracker domain without disabling Paint Lab.

## Undo history

The `HISTORY_SETTINGS` object in `app/frontend/index.html` configures
`undoSteps: 20` and `patchMemoryMB: 48`. The Undo interface only exposes the
20 most recent actions. Earlier strokes remain painted and **their original
editable actions remain in saved project documents** for compatibility.

To avoid full-replay delays, recent mobile strokes store only bounded native
resolution 128-pixel before/after tiles, not whole-canvas checkpoints. These
patches accelerate both Undo and Redo and are populated when saved artwork
is reconstructed by the gallery. The memory budget is strictly limited;
unavailable or expensive patch cases fall back to yielding raster replay.
Complex structural edits and very large strokes may still require replay,
so a short pause is possible in those exceptional cases.

This release does **not** compact project files or discard older editable
actions: truncating project history safely would require rasterizing old
painting into a new cross-version base layer representation and a distinct
project-format migration.
