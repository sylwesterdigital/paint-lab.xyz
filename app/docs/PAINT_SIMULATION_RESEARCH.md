# Painting simulation references — architectural notes

These are engineering notes based on the reference JavaScript bundles supplied on
2026-11-21. They describe observed mechanisms rather than reproducing third-party code.

## Brushwork (VR) renderer

The large client bundle contains a GPU-oriented BrushTip / painting subsystem,
not merely a visual brush-stamp library:

- **Contact geometry:** a rendered brush mesh produces a depth/contact footprint.
  Brush-tip families are represented by actual tool geometry or associated tip maps.
- **Bristle loading:** two alternating render targets hold colour currently loaded
  into the brush, rather than equating pigment to the most recently rendered pixel.
- **Pickup:** a separate pair of ping-pong pickup textures samples the existing
  painting and feeds controlled colour back into the brush reservoir.
- **Deposition:** an independent shader pass projects the contact into the
  painting texture and consults a canvas-height texture.
- **Surface height/lighting:** a heightmap gradient (Sobel-style neighbouring
  samples) influences the visible normal/lighting of accumulated paint.
- **Pigment:** the shader code includes RYB/RGB conversion as an approximation
  to subtractive paint mixing.

The supplied HTML bootstraps A-Frame/WebXR and service integrations. The additional
bundle is largely Three.js glTF-export infrastructure, not the primary source
of these painting calculations.

None of those excerpts alone establishes full Navier–Stokes fluid simulation,
real bristle elasticity, real-world paint rheology, or transferable licensing.
Their structures are a useful *design reference*, not code to paste into Paint Lab.

## Implications for Paint Lab

The existing CPU oil renderer already carries bristle RGB/load separately and
samples original underlying pigment. It does **not** maintain independent pigment
wetness and elevation per layer, or solve paint flow. Its relief is currently baked
as pixel shading rather than a height-field normal in a GPU shader.

A substantial future renderer should use separate buffers for:

1. **Tool contact and bristle shape** (width, pressure, tilt, orientation, hair stiffness).
2. **Bristle reservoir** (pigment and wetness), with bounded pickup/deposit passes.
3. **Canvas colour and wetness**, respecting each composited layer's visibility.
4. **Paint height** for raised ridges, scraping and directional surface lighting.
5. **Preview versus committed stroke**, so cancellation and multitouch never
   leave partial paint behind.

Implement in bounded dirty tiles with GPU render targets where supported,
record deterministic stroke input for editable replay, preserve a fast 2D fallback
for mobile, and measure memory/fps before enabling heavier effects.

## v0.1.29 immediate correction

The previous endpoint-only pixel eraser could leave a broad, abrupt beginning
and an inverted or squared-off tail. This release applies *tip-family-specific
contact envelopes* at both touchdown and lift-off, based on recorded trajectory,
pressure, and relative speed. It maintains the original-pigment snapshot when
retracting a contact, rather than stamping another coloured cap or inserting
black/transparent patches. Short strokes have bounded non-overlapping envelope
regions. **This is still a raster oil approximation, not a GPU paint-height solver.**
