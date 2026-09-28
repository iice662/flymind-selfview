"""Minimal pure-Python Parquet reader (no pandas / pyarrow / duckdb needed).

Supports exactly what the FlyWire materialization exports use:
  * Thrift compact protocol metadata
  * PLAIN (0), RLE_DICTIONARY (8), PLAIN_DICTIONARY (2) encoding
  * SNAPPY (1) and UNCOMPRESSED (0) codecs
  * physical types: BOOLEAN, INT32, INT64, FLOAT, DOUBLE, BYTE_ARRAY
  * optional (definition level 1) columns

Usage:
    from parquet_lite import read_parquet, read_schema
    schema = read_schema(path)
    for batch in read_parquet(path, columns=['Presynaptic_Index'], batch_rows=1_000_000):
        ...
"""
from __future__ import annotations

import struct
from typing import Iterator

# ---------------------------------------------------------------- thrift compact

CT_STOP = 0
CT_BOOLEAN_TRUE = 1
CT_BOOLEAN_FALSE = 2
CT_BYTE = 3
CT_I16 = 4
CT_I32 = 5
CT_I64 = 6
CT_DOUBLE = 7
CT_BINARY = 8
CT_LIST = 9
CT_SET = 10
CT_MAP = 11
CT_STRUCT = 12

_TYPESIZE = {CT_BOOLEAN_TRUE: 1, CT_BOOLEAN_FALSE: 1, CT_BYTE: 1, CT_I16: 2,
             CT_I32: 4, CT_I64: 8, CT_DOUBLE: 8}


class _Reader:
    __slots__ = ("b", "i")

    def __init__(self, buf: bytes, pos: int = 0):
        self.b = buf
        self.i = pos

    def byte(self) -> int:
        v = self.b[self.i]
        self.i += 1
        return v

    def varint(self) -> int:
        shift = 0
        result = 0
        while True:
            c = self.b[self.i]
            self.i += 1
            result |= (c & 0x7F) << shift
            if not (c & 0x80):
                return result
            shift += 7

    def zigzag(self) -> int:
        n = self.varint()
        return (n >> 1) ^ -(n & 1)

    def binary(self) -> bytes:
        n = self.varint()
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def double(self) -> float:
        v = struct.unpack_from("<d", self.b, self.i)[0]
        self.i += 8
        return v


def _read_struct(r: _Reader) -> dict:
    """Read a thrift compact struct into {field_id: value}."""
    out: dict = {}
    last = 0
    while True:
        h = r.byte()
        if h == CT_STOP:
            return out
        ttype = h & 0x0F
        delta = (h & 0xF0) >> 4
        if delta:
            fid = last + delta
        else:
            fid = r.zigzag()
        last = fid
        if ttype == CT_BOOLEAN_TRUE:
            out[fid] = True
        elif ttype == CT_BOOLEAN_FALSE:
            out[fid] = False
        elif ttype == CT_BYTE:
            out[fid] = struct.unpack("b", r.b[r.i:r.i + 1])[0]
            r.i += 1
        elif ttype in (CT_I16, CT_I32, CT_I64):
            out[fid] = r.zigzag()
        elif ttype == CT_DOUBLE:
            out[fid] = r.double()
        elif ttype == CT_BINARY:
            out[fid] = r.binary()
        elif ttype in (CT_LIST, CT_SET):
            out[fid] = _read_list(r)
        elif ttype == CT_MAP:
            out[fid] = _read_map(r)
        elif ttype == CT_STRUCT:
            out[fid] = _read_struct(r)
        else:
            raise ValueError("unknown thrift type %d" % ttype)


def _read_list(r: _Reader):
    h = r.byte()
    size = (h & 0xF0) >> 4
    ttype = h & 0x0F
    if size == 15:
        size = r.varint()
    if size == 0:
        return []
    if ttype == CT_STRUCT:
        return [_read_struct(r) for _ in range(size)]
    if ttype in (CT_LIST, CT_SET):
        return [_read_list(r) for _ in range(size)]
    if ttype == CT_MAP:
        return [_read_map(r) for _ in range(size)]
    if ttype in (CT_BOOLEAN_TRUE, CT_BOOLEAN_FALSE):
        return [r.byte() == 1 for _ in range(size)]
    if ttype == CT_BYTE:
        vals = list(r.b[r.i:r.i + size])
        r.i += size
        return vals
    if ttype in (CT_I16, CT_I32, CT_I64):
        return [r.zigzag() for _ in range(size)]
    if ttype == CT_DOUBLE:
        return [r.double() for _ in range(size)]
    if ttype == CT_BINARY:
        return [r.binary() for _ in range(size)]
    raise ValueError("unsupported list elem type %d" % ttype)


def _read_map(r: _Reader):
    size = r.varint()
    if size == 0:
        return {}
    h = r.byte()
    ktype, vtype = (h & 0xF0) >> 4, h & 0x0F
    out = {}
    for _ in range(size):
        k = _read_struct(r) if ktype == CT_STRUCT else r.binary()
        v = _read_struct(r) if vtype == CT_STRUCT else r.binary()
        out[k] = v
    return out


# ---------------------------------------------------------------- snappy

def _lz4_block_decompress(data: bytes, expected_size: int | None = None) -> bytes:
    """LZ4 raw block decompression (parquet codec LZ4_RAW and the HadUok blocks).

    Block format: sequences of [token][literal length ext][literals][offset][match length ext],
    where the token's high nibble is the literal length and the low nibble the match length.
    """
    out = bytearray()
    pos = 0
    n = len(data)
    while pos < n:
        token = data[pos]
        pos += 1
        # literals
        lit = token >> 4
        if lit == 15:
            while pos < n:
                e = data[pos]
                pos += 1
                lit += e
                if e != 255:
                    break
        if lit:
            out += data[pos:pos + lit]
            pos += lit
        if pos >= n:
            break  # last sequence may end after the literals
        offset = data[pos] | (data[pos + 1] << 8)
        pos += 2
        if offset == 0:
            raise ValueError("lz4: zero match offset")
        mlen = token & 0x0F
        if mlen == 15:
            while pos < n:
                e = data[pos]
                pos += 1
                mlen += e
                if e != 255:
                    break
        mlen += 4
        start = len(out) - offset
        if start < 0:
            raise ValueError("lz4: match offset %d before output start" % offset)
        if offset >= mlen:
            out += out[start:start + mlen]
        else:
            for k in range(mlen):
                out.append(out[start + k])
    if expected_size is not None and len(out) != expected_size:
        raise ValueError("lz4: got %d bytes, expected %d" % (len(out), expected_size))
    return bytes(out)


def _lz4_hadoop_decompress(data: bytes, expected_size: int | None = None) -> bytes:
    """LZ4_HADOOP (parquet codec 5): [uint32 BE uncompressed][uint32 BE compressed][block]..."""
    out = bytearray()
    pos = 0
    while pos + 8 <= len(data):
        total = struct.unpack_from(">I", data, pos)[0]
        comp = struct.unpack_from(">I", data, pos + 4)[0]
        pos += 8
        if total == 0:
            break
        out += _lz4_block_decompress(data[pos:pos + comp], total)
        pos += comp
    return bytes(out)


def _zstd_decompress(data: bytes) -> bytes:
    """ZSTD frame decompression via the Python 3.14+ stdlib `compression.zstd`."""
    from compression import zstd
    return zstd.decompress(data)


def _brotli_decompress(data: bytes) -> bytes:
    try:
        import brotli  # type: ignore
        return brotli.decompress(data)
    except ImportError as e:
        raise ValueError("brotli codec needs the `brotli` module") from e


def _snappy_decompress(data: bytes) -> bytes:
    """Snappy block-format decoder (raw, with uncompressed-length preamble).

    Parquet's SNAPPY codec stores raw snappy blocks (no stream framing), so the
    payload starts with the varint uncompressed length.
    """
    pos = 0
    shift = 0
    declared = 0
    while True:
        if pos >= len(data):
            raise ValueError("truncated snappy preamble")
        c = data[pos]
        pos += 1
        declared |= (c & 0x7F) << shift
        if not (c & 0x80):
            break
        shift += 7
    out = bytearray()
    n = len(data)
    while pos < n:
        tag = data[pos]
        pos += 1
        kind = tag & 0x03
        ln = tag >> 2
        if kind == 0:  # literal
            if ln >= 60:
                extra = ln - 59
                ln = int.from_bytes(data[pos:pos + extra], "little")
                pos += extra
            ln += 1
            out += data[pos:pos + ln]
            pos += ln
        else:
            if kind == 1:
                ln = ((tag >> 2) & 0x07) + 4
                offset = ((tag >> 5) << 8) | data[pos]
                pos += 1
            elif kind == 2:
                ln = (tag >> 2) + 1
                offset = int.from_bytes(data[pos:pos + 2], "little")
                pos += 2
            else:
                ln = (tag >> 2) + 1
                offset = int.from_bytes(data[pos:pos + 4], "little")
                pos += 4
            if offset == 0 or offset > len(out):
                raise ValueError("bad snappy offset %d (have %d bytes)" % (offset, len(out)))
            start = len(out) - offset
            if ln <= offset:
                out += out[start:start + ln]
            else:  # overlapping copy, must be byte-by-byte
                for k in range(ln):
                    out.append(out[start + k])
    return bytes(out)


# ---------------------------------------------------------------- parquet model

class Column:
    """Column chunk metadata (thrift ColumnMetaData, stored in ColumnChunk field 3)."""
    __slots__ = ("name", "physical", "type_length", "codec", "data_page_offset",
                 "dict_page_offset", "num_values", "total_compressed_size", "path")

    def __init__(self, chunk: dict, path: list[str]):
        meta = chunk.get(3, {})
        self.path = path
        self.name = ".".join(path)
        self.physical = meta.get(1)                 # 0 BOOLEAN 1 INT32 2 INT64 4 FLOAT 5 DOUBLE 6 BYTE_ARRAY
        self.type_length = meta.get(2)
        self.codec = meta.get(4, 0)                 # 0 UNCOMPRESSED 1 SNAPPY 2 GZIP 4 LZ4_RAW 5 ZSTD 6 BROTLI 7 LZ4_HADOOP
        self.num_values = meta.get(5, 0)
        self.total_compressed_size = meta.get(7, 0)
        self.data_page_offset = meta.get(9, 0)
        self.dict_page_offset = meta.get(11)


class RowGroup:
    __slots__ = ("num_rows", "columns")

    def __init__(self, meta: dict, paths: list[list[str]]):
        self.num_rows = meta.get(3, 0)
        self.columns = [Column(m, paths[i]) for i, m in enumerate(meta.get(1, []))]

def _read_footer(path: str) -> dict:
    """Read + parse the thrift footer. Raises if the file looks truncated."""
    with open(path, "rb") as f:
        size = f.seek(0, 2)
        if size < 12:
            raise ValueError("file too small to be parquet: %d bytes" % size)
        f.seek(size - 8)
        tail = f.read(8)
        if tail[4:] != b"PAR1":
            raise ValueError(
                "no PAR1 magic at EOF - file is incomplete (%d bytes downloaded so far)" % size)
        meta_len = struct.unpack("<I", tail[:4])[0]
        if meta_len <= 0 or meta_len > size - 12:
            raise ValueError("implausible footer length %d (file size %d)" % (meta_len, size))
        f.seek(size - 8 - meta_len)
        return _read_struct(_Reader(f.read(meta_len)))


def read_schema(path: str):
    return _fmt_schema(_read_footer(path)[2])


def _fmt_schema(schema_el) -> list[tuple[str, int, int]]:
    """SchemaElement: 1=type, 3=repetition_type, 4=name, 5=num_children."""
    out = []
    for el in schema_el:
        name = el[4].decode() if 4 in el else "?"
        out.append((name, el.get(5, 0), el.get(1, -1)))
    return out


def _open_meta(path: str):
    meta = _read_footer(path)
    schema_elements = meta[2]
    leaves: list[list[str]] = []

    def walk(idx: int, prefix: list[str]):
        el = schema_elements[idx]
        name = el[4].decode()
        children = el.get(5, 0)
        if children == 0:
            leaves.append(prefix + [name])
            return idx + 1
        nxt = idx + 1
        for _ in range(children):
            nxt = walk(nxt, prefix + [name])
        return nxt

    # root element is schema_elements[0] and its children cover the whole tree
    idx = 1
    for _ in range(schema_elements[0].get(5, 0)):
        if idx >= len(schema_elements):
            break
        idx = walk(idx, [])
    row_groups = [RowGroup(m, leaves) for m in meta[4]]
    return row_groups, leaves


# ---------------------------------------------------------------- page decoding

def _bit_width(max_value: int) -> int:
    w = 0
    while (1 << w) <= max_value:
        w += 1
    return w


def _decode_rle_hybrid(buf: bytes, bit_width: int, count: int) -> list[int]:
    out: list[int] = []
    pos = 0
    byte_width = (bit_width + 7) // 8
    while len(out) < count and pos < len(buf):
        header = 0
        shift = 0
        while True:
            c = buf[pos]
            pos += 1
            header |= (c & 0x7F) << shift
            if not (c & 0x80):
                break
            shift += 7
        if header & 1:  # bit-packed run
            groups = header >> 1
            nvals = groups * 8
            nbytes = groups * bit_width
            chunk = buf[pos:pos + nbytes]
            pos += nbytes
            if bit_width == 0:
                out.extend([0] * nvals)
            else:
                acc = int.from_bytes(chunk, "little")
                mask = (1 << bit_width) - 1
                for k in range(nvals):
                    out.append((acc >> (k * bit_width)) & mask)
        else:  # RLE run
            run = header >> 1
            if bit_width == 0:
                out.extend([0] * run)
            else:
                val = int.from_bytes(buf[pos:pos + byte_width], "little")
                pos += byte_width
                out.extend([val] * run)
    return out[:count]


def _decode_plain(buf: bytes, physical: int, count: int, type_length: int | None):
    if physical == 0:  # BOOLEAN
        bits = buf
        return [(bits[k >> 3] >> (k & 7)) & 1 for k in range(count)]
    if physical == 1:  # INT32
        n = min(count, len(buf) // 4)
        return list(struct.unpack_from("<%di" % n, buf, 0))
    if physical == 2:  # INT64
        n = min(count, len(buf) // 8)
        return list(struct.unpack_from("<%dq" % n, buf, 0))
    if physical == 4:  # FLOAT
        n = min(count, len(buf) // 4)
        return list(struct.unpack_from("<%df" % n, buf, 0))
    if physical == 5:  # DOUBLE
        n = min(count, len(buf) // 8)
        return list(struct.unpack_from("<%dd" % n, buf, 0))
    if physical == 6:  # BYTE_ARRAY
        out = []
        pos = 0
        for _ in range(count):
            if pos + 4 > len(buf):
                break
            ln = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
            out.append(buf[pos:pos + ln])
            pos += ln
        return out
    raise ValueError("unsupported physical type %s" % physical)


def _try_codec(decompressor, payload: bytes, page_header) -> bytes:
    """Decompress a page, falling back to the raw bytes when the codec field lies.

    Some exporters stamp a codec into the column metadata while writing the page
    bodies uncompressed (observed in the FlyWire 783 materialisation: codec says
    LZ4/ZSTD, but the payload length equals the uncompressed length and no
    compression frame is present anywhere in the file).  The declared
    uncompressed_page_size is the contract we actually rely on.
    """
    expected = page_header.get(2)
    try:
        out = decompressor(payload)
        if expected is None or len(out) == expected:
            return out
    except Exception:
        pass
    return payload


def _read_column_chunk(f, col: Column, total_rows: int) -> list:
    """Read all pages of one column chunk; returns values (nulls as None).

    PageHeader field numbers (parquet.thrift):
        1 type, 2 uncompressed_page_size, 3 compressed_page_size,
        4 data_page_header, 5 index_page_header, 6 dictionary_page_header,
        7 data_page_header_v2
    A V1 page payload is `[definition/repetition levels][values]` compressed as
    one block, so the only safe way to walk pages is end = offset + compressed size.
    """
    values: list = []
    dictionary = None

    start = col.data_page_offset
    if col.dict_page_offset:
        start = col.dict_page_offset if not start else min(start, col.dict_page_offset)
    end_of_chunk = col.data_page_offset + col.total_compressed_size if col.total_compressed_size else None

    f.seek(start)
    while len(values) < total_rows:
        offset = f.tell()
        if end_of_chunk is not None and offset >= end_of_chunk:
            break
        buf = f.read(1 << 16)
        r = _Reader(buf, 0)
        page_header = _read_struct(r)
        comp_size = page_header.get(3)
        ptype = page_header.get(1)          # 0 DATA_PAGE, 1 INDEX_PAGE, 2 DICTIONARY_PAGE, 3 DATA_PAGE_V2
        if not comp_size or comp_size < 0:
            break
        payload = f.read(comp_size)
        if len(payload) < comp_size:
            break
        raw = payload
        if col.codec == 1:
            raw = _try_codec(_snappy_decompress, payload, page_header)
        elif col.codec == 6:  # ZSTD (parquet 2.9 enum)
            raw = _try_codec(_zstd_decompress, payload, page_header)
        elif col.codec in (4, 7):  # LZ4_RAW in either enum ordering
            raw = _try_codec(lambda d: _lz4_block_decompress(d, page_header.get(2)),
                             payload, page_header)
        elif col.codec == 5:  # ZSTD in the older enum ordering / LZ4_HADOOP in the new one
            try:
                raw = _zstd_decompress(payload)
            except Exception:
                raw = _try_codec(_lz4_hadoop_decompress, payload, page_header)
        elif col.codec == 2:  # GZIP
            import gzip as _gzip
            raw = _try_codec(_gzip.decompress, payload, page_header)
        elif col.codec == 3:  # LZO - not supported
            raise ValueError("LZO codec is not supported")
        elif col.codec == 0 or col.codec is None:
            pass
        else:
            raise ValueError("unsupported codec %s" % col.codec)

        if ptype == 2:
            dph = page_header.get(6, {})
            nvals = dph.get(1, 0)
            dictionary = _decode_plain(raw, col.physical, nvals, col.type_length)
            continue
        if ptype == 3:  # DATA_PAGE_V2: levels are stored separately and never compressed
            dh = page_header.get(7, {})
            nvals = dh.get(1, 0)
            enc = dh.get(2, 0)
            def_len = dh.get(5, 0)
            rep_len = dh.get(6, 0)
            def_levels = None
            p = 0
            if def_len:
                def_levels = _decode_rle_hybrid(raw[p:p + def_len], 1, nvals)
                p += def_len
            p += rep_len
            body = raw[p:]
            _extend_values(values, body, enc, def_levels, nvals, dictionary, col)
            continue
        if ptype == 0:
            dh = page_header.get(4, {})
            nvals = dh.get(1, 0)
            enc = dh.get(2, 0)
            def_levels = None
            p = 0
            if dh.get(3):  # definition levels present (max def level > 0)
                ln = struct.unpack_from("<I", raw, p)[0]
                p += 4
                def_levels = _decode_rle_hybrid(raw[p:p + ln], 1, nvals)
                p += ln
            if dh.get(4):  # repetition levels, skipped (flat columns only)
                ln = struct.unpack_from("<I", raw, p)[0]
                p += 4
                p += ln
            _extend_values(values, raw[p:], enc, def_levels, nvals, dictionary, col)
            continue
        break  # index pages and anything else: ignore
    if len(values) < total_rows:
        raise ValueError("short column chunk %s: got %d of %d" % (col.name, len(values), total_rows))
    return values


def _extend_values(values, body, enc, def_levels, nvals, dictionary, col):
    if enc in (2, 8):  # PLAIN_DICTIONARY / RLE_DICTIONARY
        if dictionary is None:
            raise ValueError("dictionary-encoded page in %s but no dictionary page" % col.name)
        bw = _bit_width(len(dictionary) - 1)
        idxs = _decode_rle_hybrid(body, bw, nvals)
        if def_levels is None:
            values.extend(dictionary[i] for i in idxs)
        else:
            it = iter(idxs)
            for d in def_levels:
                values.append(dictionary[next(it)] if d else None)
    elif enc == 0:  # PLAIN
        if def_levels is None:
            values.extend(_decode_plain(body, col.physical, nvals, col.type_length))
        else:
            non_null = sum(1 for d in def_levels if d)
            vals = _decode_plain(body, col.physical, non_null, col.type_length)
            it = iter(vals)
            for d in def_levels:
                values.append(next(it) if d else None)
    else:
        raise ValueError("unsupported encoding %s in %s" % (enc, col.name))


def read_parquet(path: str, columns: list[str] | None = None,
                 batch_rows: int | None = None) -> Iterator[dict]:
    """Yield {column_name: [values]} batches. Rows are concatenated across row groups."""
    row_groups, leaves = _open_meta(path)
    names = [l[-1] for l in leaves]
    wanted = set(columns) if columns else set(names)
    with open(path, "rb") as f:
        for rg in row_groups:
            data = {}
            for col in rg.columns:
                if col.name not in wanted and col.name.split(".")[-1] not in wanted:
                    continue
                data[col.name.split(".")[-1]] = _read_column_chunk(f, col, rg.num_rows)
            if batch_rows is None or rg.num_rows <= batch_rows:
                yield data
            else:
                n = rg.num_rows
                for s in range(0, n, batch_rows):
                    yield {k: v[s:s + batch_rows] for k, v in data.items()}


if __name__ == "__main__":
    import sys
    p = sys.argv[1]
    print("row groups / leaves:")
    rgs, leaves = _open_meta(p)
    print("  leaves:", [l[-1] for l in leaves])
    for n, rg in enumerate(rgs):
        print("  rg%d rows=%d cols=%d" % (n, rg.num_rows, len(rg.columns)))
    for batch in read_parquet(p, batch_rows=5):
        for k, v in batch.items():
            print(" ", k, v[:5])
        break
