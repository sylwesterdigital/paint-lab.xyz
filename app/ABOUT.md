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
