"""Browser/SQLite editable-project wire format, independent of Flask.

v2/v3 remain readable. v4 was introduced by composite filter actions in v0.1.33;
older servers accepted only v2/v3 and rejected every v4 cloud save.
This module is also exercised on non-Flask preflight machines so compatibility
cannot silently regress between application/browser and server releases.
"""
from __future__ import annotations

import json
import math

DOCUMENT_FORMAT = 'paint-lab-webgl'
CURRENT_VERSION = 4
READABLE_VERSIONS = frozenset((2, 3, 4))
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_CANVAS_PIXELS = 16_000_000
ALLOWED_ACTIONS = frozenset((
    'stroke', 'shape', 'edit', 'fill', 'layer-add', 'layer-clone',
    'layer-remove', 'layer-props', 'layer-order', 'layer-transform',
    'canvas-clear', 'layer-remove-many', 'layer-props-many',
    'layer-clone-many', 'layer-merge', 'layer-filter',
))


def _dimension(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 32 <= value <= 8192:
        raise ValueError('Invalid canvas ' + label)
    return float(value)


def validate_document(obj):
    """Return safe JSON for storage; never downgrade or discard newer actions."""
    if not isinstance(obj, dict) or obj.get('format') != DOCUMENT_FORMAT:
        raise ValueError('Invalid Paint Lab project format')
    version = obj.get('version')
    if type(version) is not int or version not in READABLE_VERSIONS:
        raise ValueError('Unsupported Paint Lab project format version')
    actions = obj.get('actions')
    if not isinstance(actions, list) or len(actions) > 20_000:
        raise ValueError('Invalid project actions')
    width = _dimension(obj.get('baseW'), 'width')
    height = _dimension(obj.get('baseH'), 'height')
    if width * height > MAX_CANVAS_PIXELS:
        raise ValueError('Canvas exceeds 16 million pixels')
    count = 0
    for action in actions:
        if not isinstance(action, dict) or action.get('kind') not in ALLOWED_ACTIONS:
            raise ValueError('Invalid project action')
        if action['kind'] == 'stroke':
            points = action.get('points')
            if not isinstance(points, list) or len(points) > 300_000:
                raise ValueError('Invalid stroke points')
            count += len(points)
            if count > 1_000_000:
                raise ValueError('Project contains too many stroke samples')
            for point in points:
                if not isinstance(point, dict) or any(type(point.get(k)) not in (float, int) or not math.isfinite(point[k]) for k in ('x', 'y')):
                    raise ValueError('Invalid stroke coordinates')
        elif action['kind'] == 'layer-filter':
            filters = action.get('filters')
            if not isinstance(filters, list) or len(filters) > 16:
                raise ValueError('Invalid layer filter stack')
            if any(not isinstance(f, dict) or not isinstance(f.get('kind'), str) or len(f['kind']) > 40 for f in filters):
                raise ValueError('Invalid layer filter settings')
    try:
        raw = json.dumps(obj, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Project contains invalid data') from exc
    if len(raw.encode('utf-8')) > MAX_JSON_BYTES:
        raise ValueError('Project exceeds 16 MB of editable history')
    return raw
