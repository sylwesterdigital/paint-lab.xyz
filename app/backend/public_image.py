"""Validate public PNG wire payloads without Flask or external image libraries."""
from __future__ import annotations
import base64,binascii,struct,zlib

def check_public_png(data, *, limit=7*1024*1024):
    """Validate actual PNG structure before storing a public image.

    Browser exports are PNG; PNG files contain CRC-protected chunks. This
    checks the payload without PIL, decompressing user-supplied image streams,
    or exposing editable project JSON in a public publication.
    """
    if not isinstance(data,str) or len(data)>limit*1.4+256 or not data.startswith('data:image/png;base64,'):
        raise ValueError('Provide a PNG image smaller than 7 MB')
    try:raw=base64.b64decode(data.split(',',1)[1],validate=True)
    except (binascii.Error,ValueError):raise ValueError('Invalid PNG encoding')
    if len(raw)>limit or len(raw)<57 or raw[:8]!=b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid or oversized PNG')
    offset=8;has_image=False;ended=False;width=height=None
    while offset < len(raw):
        if offset+12>len(raw):raise ValueError('Truncated PNG')
        size=struct.unpack_from('>I',raw,offset)[0];kind=raw[offset+4:offset+8]
        end=offset+12+size
        if size>limit or end>len(raw):raise ValueError('Truncated PNG')
        chunk=raw[offset+8:offset+8+size]
        expected=struct.unpack_from('>I',raw,offset+8+size)[0]
        if (zlib.crc32(kind+chunk)&0xffffffff)!=expected:
            raise ValueError('Corrupt PNG chunk')
        if offset==8:
            if kind!=b'IHDR' or size!=13:raise ValueError('Invalid PNG header')
            width,height,depth,color,compression,filter_method,interlace=struct.unpack('>IIBBBBB',chunk)
            if not 1<=width<=8192 or not 1<=height<=8192 or width*height>16_000_000:
                raise ValueError('Unsupported image dimensions')
            if (depth,color) not in ((1,0),(2,0),(4,0),(8,0),(16,0),(8,2),(16,2),(1,3),(2,3),(4,3),(8,3),(8,4),(16,4),(8,6),(16,6)) or compression or filter_method or interlace not in (0,1):
                raise ValueError('Unsupported PNG colour format')
        if kind==b'IDAT':has_image=True
        if kind==b'IEND':
            if size!=0 or end!=len(raw):raise ValueError('Invalid PNG trailer')
            ended=True;break
        offset=end
    if not has_image or not ended:raise ValueError('Incomplete PNG image')
    return raw

