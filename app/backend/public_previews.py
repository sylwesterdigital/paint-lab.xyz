"""Bounded, on-demand WebP previews for public Paint Lab PNGs.

Only the application-selected filename is used; no client paths are accepted.
Preview files live beside, not inside, the versioned application release.
"""
from __future__ import annotations

import io, os, struct, threading
from pathlib import Path

MAX_DIMENSION = 720
WEBP_QUALITY = 76
_LOCK = threading.Lock()


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read dimensions cheaply without decoding full-sized PNG artwork."""
    try:
        with path.open('rb') as stream:
            header = stream.read(24)
        if header[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR':
            return (1, 1)
        width, height = struct.unpack('>II', header[16:24])
        if not 1 <= width <= 8192 or not 1 <= height <= 8192:
            return (1, 1)
        return width, height
    except (OSError, ValueError, struct.error):
        return (1, 1)


def preview_path(public_dir: Path, token: str) -> Path:
    return public_dir / 'previews' / (token + '.webp')


def make_preview(source: Path, destination: Path) -> Path:
    """Generate a transparent, aspect-correct preview once; atomic replace.

    A lock prevents concurrent Flask threads re-encoding the same file. PNG remains
    the canonical/full-resolution original; no database changes are required.
    """
    if destination.exists():
        return destination
    with _LOCK:
        if destination.exists():
            return destination
        from PIL import Image, ImageOps
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with Image.open(source) as input_image:
            if input_image.format != 'PNG' or input_image.width * input_image.height > 16_000_000:
                raise ValueError('Unsupported public image')
            img = ImageOps.exif_transpose(input_image)
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            tmp = destination.with_name(destination.name + '.' + str(os.getpid()) + '.tmp')
            try:
                img.save(tmp, 'WEBP', quality=WEBP_QUALITY, method=4)
                tmp.chmod(0o600)
                os.replace(tmp, destination)
            finally:
                tmp.unlink(missing_ok=True)
    return destination
