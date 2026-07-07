# ═══════════════════════════════════════════════════════
#  Henriquix20 Encoder — patcher.py
#  10x sample-count amplifier for TikTok uploads.
#  Python port of Pascha's buildPaschaPatch() logic.
# ═══════════════════════════════════════════════════════

import struct

FAKE_SAMPLE = bytes([0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00])


# ── Primitive readers / writers ──────────────────────────

def _r32(b, o):   return struct.unpack_from('>I', b, o)[0]
def _ri32(b, o):  return struct.unpack_from('>i', b, o)[0]
def _r64(b, o):
    hi, lo = struct.unpack_from('>II', b, o)
    return hi * 4294967296 + lo
def _ri64(b, o):
    hi, lo = struct.unpack_from('>iI', b, o)
    return hi * 4294967296 + lo

def _w32(b, o, v):  struct.pack_into('>I', b, o, int(v) & 0xFFFFFFFF)
def _wi32(b, o, v): struct.pack_into('>i', b, o, int(v))
def _w64(b, o, v):
    v   = int(v)
    hi  = v >> 32
    lo  = v & 0xFFFFFFFF
    struct.pack_into('>II', b, o, hi, lo)

def _fourcc(b, o=0):
    return b[o+4:o+8].decode('latin-1')


# ── Box helpers ──────────────────────────────────────────

def _hdr(b, o=0):
    """Return (size, header_len) for box at offset o."""
    s = _r32(b, o)
    if s == 1:
        return _r64(b, o+8), 16
    if s == 0:
        return len(b) - o, 8
    return s, 8

def _parse_boxes(b, start, end):
    out, pos = [], start
    while pos + 8 <= end:
        s, h = _hdr(b, pos)
        t    = _fourcc(b, pos)
        if s < h or pos + s > end:
            break
        out.append({'type': t, 'start': pos, 'end': pos+s, 'hl': h})
        pos += s
    return out

def _header_size(b):
    return 16 if _r32(b, 0) == 1 else 8

def _child_start(b):
    h = _header_size(b)
    return h + (4 if _fourcc(b) == 'meta' else 0)

def _children(b):
    return _parse_boxes(b, _child_start(b), len(b))

def _find_child(b, typ):
    for c in _children(b):
        if c['type'] == typ:
            return b[c['start']:c['end']]
    return None

def _find_path(b, path):
    cur = b
    for t in path:
        cur = _find_child(cur, t)
        if cur is None:
            return None
    return cur

def _make_box(typ, payload, large=False):
    if isinstance(typ, str):
        typ = typ.encode('latin-1')
    if large:
        size = 16 + len(payload)
        out  = bytearray(size)
        _w32(out, 0, 1)
        out[4:8] = typ
        _w64(out, 8, size)
        out[16:] = payload
    else:
        size = 8 + len(payload)
        out  = bytearray(size)
        _w32(out, 0, size)
        out[4:8] = typ
        out[8:]  = payload
    return bytes(out)

def _rebuild(b, map_child):
    t   = _fourcc(b)
    h   = _header_size(b)
    cs  = _child_start(b)
    pfx = b[h:cs]
    parts = [pfx]
    for c in _parse_boxes(b, cs, len(b)):
        child = b[c['start']:c['end']]
        parts.append(map_child(child, c['type']))
    return _make_box(t, b''.join(parts), h == 16)

def _concat(parts):
    return b''.join(parts)


# ── Box parsers ──────────────────────────────────────────

def _handler_type(trak):
    hdlr = _find_path(trak, ['mdia', 'hdlr'])
    if not hdlr:
        return ''
    h = _header_size(hdlr)
    return hdlr[h+8:h+12].decode('latin-1')

def _stsd_codec(stsd):
    if not stsd:
        return ''
    entry_count = _r32(stsd, 12)
    if not entry_count:
        return ''
    return _fourcc(stsd, 16)   # first sample entry fourcc

def _parse_mvhd(mvhd):
    h = _header_size(mvhd)
    v = mvhd[h]
    if v == 0:
        return {'version': v, 'timescale': _r32(mvhd, h+12), 'duration': _r32(mvhd, h+16)}
    return     {'version': v, 'timescale': _r32(mvhd, h+20), 'duration': _r64(mvhd, h+24)}

def _patch_mvhd(mvhd, new_duration):
    out = bytearray(mvhd)
    h   = _header_size(mvhd)
    v   = mvhd[h]
    if v == 0: _w32(out, h+16, new_duration)
    else:      _w64(out, h+24, new_duration)
    return bytes(out)

def _parse_tkhd(tkhd):
    h = _header_size(tkhd)
    v = tkhd[h]
    w_off = 84 if v == 0 else 96
    return {
        'version':  v,
        'duration': _r32(tkhd, h+20) if v == 0 else _r64(tkhd, h+28),
        'width':    _r32(tkhd, w_off)  / 65536,
        'height':   _r32(tkhd, w_off+4) / 65536,
    }

def _patch_tkhd(tkhd, new_duration):
    out = bytearray(tkhd)
    h   = _header_size(tkhd)
    v   = tkhd[h]
    if v == 0: _w32(out, h+20, new_duration)
    else:      _w64(out, h+28, new_duration)
    return bytes(out)

def _parse_mdhd(mdhd):
    h = _header_size(mdhd)
    v = mdhd[h]
    if v == 0:
        return {'version': v, 'timescale': _r32(mdhd, h+12), 'duration': _r32(mdhd, h+16)}
    return     {'version': v, 'timescale': _r32(mdhd, h+20), 'duration': _r64(mdhd, h+24)}

def _patch_mdhd(mdhd, new_duration):
    out = bytearray(mdhd)
    h   = _header_size(mdhd)
    v   = mdhd[h]
    if v == 0: _w32(out, h+16, new_duration)
    else:      _w64(out, h+24, new_duration)
    return bytes(out)

def _parse_stts(stts):
    n = _r32(stts, 12)
    sample_count = total_ticks = last_delta = 0
    delta_weight = {}
    for i in range(n):
        o = 16 + i*8
        c = _r32(stts, o)
        d = _r32(stts, o+4)
        sample_count += c
        total_ticks  += c * d
        last_delta    = d
        delta_weight[d] = delta_weight.get(d, 0) + c
    primary_delta = last_delta
    best = -1
    for delta, count in delta_weight.items():
        if count > best:
            best = count
            primary_delta = delta
    return {'entry_count': n, 'sample_count': sample_count,
            'total_ticks': total_ticks, 'last_delta': last_delta,
            'primary_delta': primary_delta}

def _parse_stsz(stsz):
    sample_size  = _r32(stsz, 12)
    sample_count = _r32(stsz, 16)
    trailing_eight = 0
    if sample_size == 0:
        for i in range(sample_count - 1, max(-1, sample_count - 5001), -1):
            if _r32(stsz, 20 + i*4) == 8:
                trailing_eight += 1
            else:
                break
    return {'sample_size': sample_size, 'sample_count': sample_count,
            'trailing_eight': trailing_eight}

def _parse_stsc(stsc):
    n = _r32(stsc, 12)
    if not n:
        raise ValueError('Video stsc has no entries.')
    o = 16 + (n-1)*12
    return {'entry_count': n,
            'last_first_chunk':      _r32(stsc, o),
            'last_samples_per_chunk': _r32(stsc, o+4),
            'last_desc_id':           _r32(stsc, o+8)}

def _parse_chunk_table(stco):
    return {'type': _fourcc(stco), 'count': _r32(stco, 12)}

def _parse_elst(elst):
    if not elst:
        return None
    h = _header_size(elst)
    v = elst[h]
    entry_count = _r32(elst, 12)
    if not entry_count:
        return None
    if v == 0:
        return {'version': v, 'entry_count': entry_count,
                'segment_duration': _r32(elst, 16), 'media_time': _ri32(elst, 20)}
    return     {'version': v, 'entry_count': entry_count,
                'segment_duration': _r64(elst, 16), 'media_time': _ri64(elst, 24)}

def _patch_elst(elst, new_segment_duration):
    out = bytearray(elst)
    h   = _header_size(elst)
    v   = elst[h]
    if v == 0: _w32(out, 16, new_segment_duration)
    else:      _w64(out, 16, new_segment_duration)
    return bytes(out)


# ── Table patchers ───────────────────────────────────────

def _patch_stts(stts, fake_count, fake_delta):
    n    = _r32(stts, 12)
    if not n:
        raise ValueError('Cannot patch empty stts.')
    last = 16 + (n-1)*8
    last_delta = _r32(stts, last+4)
    if last_delta == fake_delta:
        out = bytearray(stts)
        _w32(out, last, _r32(stts, last) + fake_count)
        return bytes(out)
    old = stts[_header_size(stts):]
    pay = bytearray(len(old) + 8)
    pay[:len(old)] = old
    _w32(pay, 4, n+1)
    o = len(old)
    _w32(pay, o,   fake_count)
    _w32(pay, o+4, fake_delta)
    return _make_box('stts', bytes(pay), _header_size(stts) == 16)

def _patch_ctts(ctts, fake_count):
    n = _r32(ctts, 12)
    if not n:
        return ctts
    last   = 16 + (n-1)*8
    h      = _header_size(ctts)
    v      = ctts[h]
    last_o = _r32(ctts, last+4) if v == 0 else _ri32(ctts, last+4)
    if last_o == 0:
        out = bytearray(ctts)
        _w32(out, last, _r32(ctts, last) + fake_count)
        return bytes(out)
    old = ctts[h:]
    pay = bytearray(len(old) + 8)
    pay[:len(old)] = old
    _w32(pay, 4, n+1)
    o = len(pay) - 8
    _w32(pay, o,   fake_count)
    _w32(pay, o+4, 0)
    return _make_box('ctts', bytes(pay), h == 16)

def _patch_sdtp(sdtp, fake_count):
    h   = _header_size(sdtp)
    old = sdtp[h:]
    pay = bytearray(len(old) + fake_count)
    pay[:len(old)] = old
    for i in range(len(old), len(pay)):
        pay[i] = 0x10
    return _make_box('sdtp', bytes(pay), h == 16)

def _patch_stsz(stsz, fake_count):
    h   = _header_size(stsz)
    old = stsz[h:]
    pay = bytearray(len(old) + fake_count*4)
    pay[:len(old)] = old
    old_count = _r32(stsz, 16)
    _w32(pay, 8, old_count + fake_count)  # payload offset 8 = sample_count
    o = len(old)
    for i in range(fake_count):
        _w32(pay, o + i*4, 8)
    return _make_box('stsz', bytes(pay), h == 16)

def _patch_stsc(stsc, first_chunk, desc_id):
    h   = _header_size(stsc)
    old = stsc[h:]
    pay = bytearray(len(old) + 12)
    pay[:len(old)] = old
    n = _r32(stsc, 12)
    _w32(pay, 4, n+1)             # payload offset 4 = entry_count
    o = len(old)
    _w32(pay, o,   first_chunk)
    _w32(pay, o+4, 1)             # 1 sample per fake chunk
    _w32(pay, o+8, desc_id)
    return _make_box('stsc', bytes(pay), h == 16)

def _patch_chunk_offsets(stco, shift, append_offset, repeat_count=1):
    t         = _fourcc(stco)
    h         = _header_size(stco)
    step      = 8 if t == 'co64' else 4
    old_count = _r32(stco, 12)
    add       = repeat_count if append_offset is not None else 0
    old       = stco[h:]
    pay       = bytearray(len(old) + add*step)
    pay[:len(old)] = old
    _w32(pay, 4, old_count + add)
    for i in range(old_count):
        po  = 8 + i*step
        old_val = _r64(stco, h+po) if step == 8 else _r32(stco, h+po)
        val     = old_val + shift
        if step == 8: _w64(pay, po, val)
        else:         _w32(pay, po, val)
    if append_offset is not None:
        for i in range(add):
            po = 8 + (old_count+i)*step
            if step == 8: _w64(pay, po, append_offset)
            else:         _w32(pay, po, int(append_offset) & 0xFFFFFFFF)
    return _make_box(t, bytes(pay), h == 16)


# ── Moov analyzer ────────────────────────────────────────

def _analyze_moov(moov):
    mvhd = _find_child(moov, 'mvhd')
    if not mvhd:
        raise ValueError('No mvhd atom found.')
    movie = _parse_mvhd(mvhd)
    if not movie['timescale']:
        raise ValueError('Movie timescale is zero.')

    video = None
    for c in _children(moov):
        if c['type'] != 'trak':
            continue
        trak = moov[c['start']:c['end']]
        if _handler_type(trak) != 'vide':
            continue
        tkhd = _find_child(trak, 'tkhd')
        mdhd = _find_path(trak, ['mdia', 'mdhd'])
        stbl = _find_path(trak, ['mdia', 'minf', 'stbl'])
        if not tkhd or not mdhd or not stbl:
            continue
        stsd = _find_child(stbl, 'stsd')
        stsz = _find_child(stbl, 'stsz')
        stts = _find_child(stbl, 'stts')
        stsc = _find_child(stbl, 'stsc')
        stco = _find_child(stbl, 'stco') or _find_child(stbl, 'co64')
        if not all([stsz, stts, stsc, stco]):
            raise ValueError('Video track is missing stsz/stts/stsc/stco atoms.')
        codec = _stsd_codec(stsd)
        if codec not in ('avc1', 'avc3'):
            raise ValueError(f'Video codec is {codec or "unknown"}, not avc1/avc3. Patch is H.264-only.')
        tk = _parse_tkhd(tkhd)
        md = _parse_mdhd(mdhd)
        ts = _parse_stts(stts)
        sz = _parse_stsz(stsz)
        sc = _parse_stsc(stsc)
        co = _parse_chunk_table(stco)
        if sz['sample_size'] != 0:
            raise ValueError('Fixed-size stsz not supported.')
        if ts['sample_count'] != sz['sample_count']:
            raise ValueError(f"stts ({ts['sample_count']}) != stsz ({sz['sample_count']}) sample count.")
        if not ts['primary_delta']:
            raise ValueError('Could not read frame delta from stts.')
        elst = _parse_elst(_find_path(trak, ['edts', 'elst']))
        video = {'codec': codec, 'tkhd': tk, 'mdhd': md,
                 'stts': ts, 'stsz': sz, 'stsc': sc,
                 'chunks': co, 'elst': elst}
        break

    if not video:
        raise ValueError('No AVC/H.264 video track found.')

    frame_rate    = video['mdhd']['timescale'] / video['stts']['primary_delta']
    target_frames = video['stsz']['sample_count'] * 10
    fake_count    = target_frames - video['stsz']['sample_count']
    if fake_count < 1:
        raise ValueError('Target sample count not higher than current. Nothing to patch.')
    if fake_count > 250000:
        raise ValueError(f'Refusing to add {fake_count} fake samples — file too large.')

    fake_ticks     = fake_count * video['stts']['primary_delta']
    new_stts_total = video['stts']['total_ticks'] + fake_ticks

    return {'movie': movie, 'video': video,
            'frame_rate': frame_rate,
            'target_frames': target_frames,
            'fake_count': fake_count,
            'fake_ticks': fake_ticks,
            'new_stts_total': new_stts_total}


# ── Moov rebuilder ───────────────────────────────────────

def _build_patched_moov(moov, info, shift_existing, fake_chunk_offset):
    fake_count = info['fake_count']
    vi         = info['video']

    def rebuild_stbl(stbl, is_video):
        def patch(child, t):
            if t in ('stco', 'co64'):
                return _patch_chunk_offsets(
                    child, shift_existing,
                    fake_chunk_offset if is_video else None,
                    fake_count if is_video else 1,
                )
            if not is_video:
                return child
            if t == 'stts': return _patch_stts(child, fake_count, vi['stts']['primary_delta'])
            if t == 'ctts': return _patch_ctts(child, fake_count)
            if t == 'sdtp': return _patch_sdtp(child, fake_count)
            if t == 'stsz': return _patch_stsz(child, fake_count)
            if t == 'stsc': return _patch_stsc(child, vi['chunks']['count']+1, vi['stsc']['last_desc_id'])
            return child
        return _rebuild(stbl, patch)

    def rebuild_minf(minf, is_video):
        return _rebuild(minf, lambda c,t: rebuild_stbl(c, is_video) if t == 'stbl' else c)

    def rebuild_mdia(mdia, is_video):
        return _rebuild(mdia, lambda c,t: rebuild_minf(c, is_video) if t == 'minf' else c)

    def rebuild_trak(trak):
        is_video = _handler_type(trak) == 'vide'
        return _rebuild(trak, lambda c,t: rebuild_mdia(c, is_video) if t == 'mdia' else c)

    def patch_moov_child(c, t):
        if t == 'trak':
            return rebuild_trak(c)
        return c

    return _rebuild(moov, patch_moov_child)


def _patch_mdat(mdat, fake_data):
    h        = _header_size(mdat)
    old_size = _r64(mdat, 8) if _r32(mdat, 0) == 1 else _r32(mdat, 0)
    if _r32(mdat, 0) == 0:
        raise ValueError('mdat size=0 not supported.')
    new_size = old_size + len(fake_data)
    out      = bytearray(len(mdat) + len(fake_data))
    out[:len(mdat)]  = mdat
    out[len(mdat):]  = fake_data
    if h == 16:
        _w64(out, 8, new_size)
    else:
        _w32(out, 0, new_size)
    return bytes(out)


# ══════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════

def get_fps(file_path):
    """Read FPS from MP4 without ffprobe. Returns float or None."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        top    = _parse_boxes(data, 0, len(data))
        moov_b = next((b for b in top if b['type'] == 'moov'), None)
        if not moov_b:
            return None
        moov   = data[moov_b['start']:moov_b['end']]
        info   = _analyze_moov(moov)
        return info.get('frame_rate')
    except Exception:
        return None


def patch_file(file_path, log_cb=None):
    """
    Apply 10x sample-count patch to an MP4.
    Overwrites file_path in place.
    Returns True on success, False on failure.
    """
    def log(msg):
        if log_cb: log_cb(msg)

    log('Reading file...')
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except OSError as e:
        log(f'ERROR: {e}')
        return False

    try:
        top = _parse_boxes(data, 0, len(data))
    except Exception as e:
        log(f'ERROR parsing file: {e}')
        return False

    moov_b = next((b for b in top if b['type'] == 'moov'), None)
    mdat_b = next((b for b in top if b['type'] == 'mdat'), None)
    if not moov_b:
        log('ERROR: moov atom not found.')
        return False
    if not mdat_b:
        log('ERROR: mdat atom not found.')
        return False

    moov_bytes = data[moov_b['start']:moov_b['end']]
    mdat_bytes = data[mdat_b['start']:mdat_b['end']]

    try:
        info = _analyze_moov(moov_bytes)
    except Exception as e:
        log(f'ERROR: {e}')
        return False

    sz = info['video']['stsz']
    if sz['trailing_eight'] >= 100 and sz['trailing_eight'] > sz['sample_count'] * 0.08:
        log(f"WARNING: file may already be patched ({sz['trailing_eight']} trailing 8-byte samples).")

    log(f"Samples:   {sz['sample_count']} real → +{info['fake_count']} fake (10x)")
    log(f"FPS:       {info['frame_rate']:.2f}")

    # Trial moov to measure delta
    try:
        trial      = _build_patched_moov(moov_bytes, info, 0, 0)
    except Exception as e:
        log(f'ERROR building moov: {e}')
        return False

    moov_delta     = len(trial) - len(moov_bytes)
    moov_before    = moov_b['start'] < mdat_b['start']
    shift          = moov_delta if moov_before else 0
    old_mdat_hdr   = mdat_b['hl']
    old_mdat_data  = mdat_b['end'] - mdat_b['start'] - old_mdat_hdr
    new_mdat_start = mdat_b['start'] + (moov_delta if moov_before else 0)
    fake_offset    = new_mdat_start + old_mdat_hdr + old_mdat_data

    try:
        final_moov = _build_patched_moov(moov_bytes, info, shift, fake_offset)
        final_mdat = _patch_mdat(mdat_bytes, FAKE_SAMPLE)
    except Exception as e:
        log(f'ERROR patching: {e}')
        return False

    parts = []
    for b in top:
        if b['type'] == 'moov':   parts.append(final_moov)
        elif b['type'] == 'mdat': parts.append(final_mdat)
        else:                     parts.append(data[b['start']:b['end']])

    output = b''.join(parts)

    try:
        with open(file_path, 'wb') as f:
            f.write(output)
    except OSError as e:
        log(f'ERROR writing: {e}')
        return False

    log(f'Done — {len(data)/1024/1024:.1f} MB → {len(output)/1024/1024:.1f} MB')
    return True