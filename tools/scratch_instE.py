"""Minimal pure-Python Apache Arrow IPC / Feather v2 reader.

MaleCNS ships its tables as `.feather` (Arrow IPC file format) and this box has no
pyarrow, so the format is read directly.  Only what these tables need:

  * "ARROW1\\0\\0" magic, message frames, footer, trailing "ARROW1"
  * Schema / RecordBatch / DictionaryBatch messages
  * primitive, utf8/binary, list<T>, struct and dictionary-encoded columns
  * buffer compression: none / LZ4_FRAME / ZSTD

Flatbuffer rules used here (this is where a naive reader goes wrong):
  * a "uoffset" is relative to *the position of the uoffset field itself*
  * a table starts with a soffset; the vtable lives at `table_pos - soffset`
  * a vector's length is stored just before its elements; a vector field's uoffset
    points at that length slot

Usage:
    from feather_lite import FeatherFile
    f = FeatherFile(path)
    print(f.schema_summary())
    data = f.read_all(columns=["bodyId", "type"])
"""
from __future__ import annotations

import struct
import sys
from typing import Iterator

# Arrow Type union ids
(T_NONE, T_NULL, T_INT, T_FLOATINGPOINT, T_BINARY, T_UTF8, T_BOOL, T_DECIMAL, T_DATE,
 T_TIME, T_TIMESTAMP, T_INTERVAL, T_LIST, T_STRUCT, T_UNION, T_FIXED_SIZE_BINARY,
 T_FIXED_SIZE_LIST, T_MAP, T_DURATION, T_LARGE_BINARY, T_LARGE_UTF8, T_LARGE_LIST,
 T_RUN_END_ENCODED, T_BINARY_VIEW, T_UTF8_VIEW, T_LIST_VIEW, T_LARGE_LIST_VIEW) = range(27)

COMPRESSION_NONE, COMPRESSION_LZ4, COMPRESSION_ZSTD = 0, 1, 2

# MessageHeader union tags, from Arrow's Message.fbs: `union MessageHeader { Schema,
# DictionaryBatch, RecordBatch, Tensor, SparseTensor }`.  The tags start at 1 because 0
# is the union's NONE member -- so Schema is 1, DictionaryBatch 2 and RecordBatch 3.
# Getting these off by one makes a reader treat the schema frame as a dictionary batch.
MSG_SCHEMA, MSG_DICTIONARY_BATCH, MSG_RECORD_BATCH = 1, 2, 3

TYPE_NAMES = {T_INT: "int", T_FLOATINGPOINT: "float", T_BINARY: "binary", T_UTF8: "utf8",
              T_BOOL: "bool", T_LIST: "list", T_STRUCT: "struct", T_LARGE_UTF8: "large_utf8",
              T_LARGE_LIST: "large_list", T_DECIMAL: "decimal",
              T_FIXED_SIZE_BINARY: "fixed_binary"}


class Table:
    """A flatbuffer table.

    `Table(buf, uoffset_pos)` follows the uoffset stored at `uoffset_pos` (flatbuffers
    root/table references work that way); `Table.at(buf, addr)` takes the table
    address directly.  A table starts with a soffset to its vtable.
    """

    __slots__ = ("buf", "pos", "vtable", "vlen")

    def __init__(self, buf: bytes, uoffset_pos: int):
        self._init(buf, uoffset_pos + struct.unpack_from("<I", buf, uoffset_pos)[0])

    @classmethod
    def at(cls, buf: bytes, addr: int) -> "Table":
        t = cls.__new__(cls)
        t._init(buf, addr)
        return t

    def _init(self, buf: bytes, pos: int):
        self.buf = buf
        self.pos = pos
        soffset = struct.unpack_from("<i", buf, pos)[0]
        self.vtable = pos - soffset
        if not (0 <= self.vtable < len(buf) - 2):
            raise ValueError("flatbuffer: bad vtable for table at %d (soffset %d)" % (pos, soffset))
        self.vlen = struct.unpack_from("<H", buf, self.vtable)[0]
        if self.vlen < 4 or self.vlen % 2 or self.vtable + self.vlen > len(buf):
            raise ValueError("flatbuffer: implausible vtable length %d at %d" % (self.vlen, self.vtable))

    # ---- low level
    def _slot(self, field_index: int) -> int | None:
        """Absolute address of a field's value, or None when the field is absent."""
        entry = 4 + field_index * 2
        if entry + 2 > self.vlen:
            return None
        voff = struct.unpack_from("<H", self.buf, self.vtable + entry)[0]
        if voff == 0:
            return None
        return self.pos + voff

    def field_count(self) -> int:
        return max(0, (self.vlen - 4) // 2)

    def present_fields(self) -> list[int]:
        return [i for i in range(self.field_count()) if self._slot(i) is not None]

    # ---- scalars
    def i8(self, fi, default=0):
        at = self._slot(fi)
        return default if at is None else struct.unpack_from("<b", self.buf, at)[0]

    def i16(self, fi, default=0):
        at = self._slot(fi)
        return default if at is None else struct.unpack_from("<h", self.buf, at)[0]

    def i32(self, fi, default=0):
        at = self._slot(fi)
        return default if at is None else struct.unpack_from("<i", self.buf, at)[0]

    def i64(self, fi, default=0):
        at = self._slot(fi)
        return default if at is None else struct.unpack_from("<q", self.buf, at)[0]

    def bool_(self, fi, default=False):
        at = self._slot(fi)
        return default if at is None else self.buf[at] != 0

    # ---- references
    def _deref(self, fi) -> int | None:
        at = self._slot(fi)
        if at is None:
            return None
        return at + struct.unpack_from("<I", self.buf, at)[0]

    def table(self, fi) -> "Table | None":
        target = self._deref(fi)
        if target is None or not (0 <= target < len(self.buf) - 4):
            return None
        try:
            return Table.at(self.buf, target)
        except ValueError:
            return None

    def string(self, fi) -> str | None:
        target = self._deref(fi)
        if target is None or target + 4 > len(self.buf):
            return None
        n = struct.unpack_from("<I", self.buf, target)[0]
        return self.buf[target + 4:target + 4 + n].decode("utf-8", "replace")

    # ---- vectors
    def _vector(self, fi):
        """-> (element_base, count) or (None, 0)."""
        target = self._deref(fi)
        if target is None or target + 4 > len(self.buf):
            return None, 0
        return target + 4, struct.unpack_from("<I", self.buf, target)[0]

    def vector_len(self, fi) -> int:
        return self._vector(fi)[1]

    def vector_table(self, fi, index: int) -> "Table | None":
        base, n = self._vector(fi)
        if base is None or index >= n:
            return None
        elem = base + index * 4
        target = elem + struct.unpack_from("<I", self.buf, elem)[0]
        if not (0 <= target < len(self.buf) - 4):
            return None
        try:
            return Table.at(self.buf, target)
        except ValueError:
            return None

    def vector_struct_i64(self, fi, index: int, size: int, field_offset: int) -> int:
        base, n = self._vector(fi)
        if base is None or index >= n:
            return 0
        return struct.unpack_from("<q", self.buf, base + index * size + field_offset)[0]

    def _struct_i64(self, table: "Table", fi, index: int, size: int, field_offset: int) -> int:
        return table.vector_struct_i64(fi, index, size, field_offset)

    def vector_struct_i32(self, fi, index: int, size: int, field_offset: int) -> int:
        base, n = self._vector(fi)
        if base is None or index >= n:
            return 0
        return struct.unpack_from("<i", self.buf, base + index * size + field_offset)[0]


# --------------------------------------------------------------------- decompression

def _lz4_block(data: bytes, expected: int | None = None, prefix: bytes = b"") -> bytes:
    """LZ4 raw block (token/offset sequences).

    `prefix` is the already-decoded data from previous blocks of the same frame:
    LZ4 frames default to *linked* blocks, so a match offset may reach back into
    earlier blocks.  Matches are resolved against `prefix + out`.
    """
    out = bytearray()
    base = len(prefix)
    window = prefix + b""          # concatenated lazily below
    pos = 0
    n = len(data)
    while pos < n:
        token = data[pos]
        pos += 1
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
            break
        offset = data[pos] | (data[pos + 1] << 8)
        pos += 2
        mlen = token & 0x0F
        if mlen == 15:
            while pos < n:
                e = data[pos]
                pos += 1
                mlen += e
                if e != 255:
                    break
        mlen += 4
        total = base + len(out)
        if offset == 0 or offset > total:
            raise ValueError("lz4: bad offset %d (have %d bytes)" % (offset, total))
        start = total - offset
        if start >= base:
            # entirely inside this block's own output
            s = start - base
            if mlen <= offset:
                out += out[s:s + mlen]
            else:
                for k in range(mlen):
                    out.append(out[s + k])
        else:
            # the match starts in an earlier block
            for k in range(mlen):
                idx = start + k
                if idx < base:
                    out.append(prefix[idx])
                else:
                    out.append(out[idx - base])
    if expected is not None and len(out) != expected:
        raise ValueError("lz4: %d bytes, expected %d" % (len(out), expected))
    return bytes(out)


def _lz4_frame(data: bytes) -> bytes:
    """LZ4 frame (magic 0x184D2204) as written by Arrow's LZ4_FRAME codec.

    Arrow uses linked blocks (FLG bit 5 clear), so the decoder keeps the full
    decoded output around and passes it as the dictionary for the next block.
    """
    if data[:4] != bytes.fromhex("04224d18"):
        raise ValueError("not an lz4 frame")
    pos = 4
    flg = data[pos]; pos += 1
    bd = data[pos]; pos += 1
    if flg & 0x08:                 # content size
        pos += 8
    if flg & 0x01:                 # dictionary id
        pos += 4
    pos += 1                       # header checksum
    out = bytearray()
    while pos + 4 <= len(data):
        block = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if block == 0:             # end mark
            break
        uncompressed = bool(block & 0x80000000)
        size = block & 0x7FFFFFFF
        chunk = data[pos:pos + size]
        pos += size
        out += chunk if uncompressed else _lz4_block(chunk, None, bytes(out))
        if flg & 0x10:             # block checksum
            pos += 4
    return bytes(out)


def decompress(codec: int, data: bytes, uncompressed_len: int) -> bytes:
    if codec == COMPRESSION_NONE:
        return data
    if codec == COMPRESSION_LZ4:
        return _lz4_frame(data)
    if codec == COMPRESSION_ZSTD:
        from compression import zstd
        return zstd.decompress(data)
    raise ValueError("unsupported buffer codec %d" % codec)


# --------------------------------------------------------------------- reader

class Field:
    __slots__ = ("name", "type_id", "children", "dictionary_id", "bit_width",
                 "byte_width", "nullable", "index", "type_table")

    def __init__(self):
        self.name = ""
        self.type_id = T_NONE
        self.children: list[Field] = []
        self.dictionary_id = None
        self.bit_width = 0
        self.byte_width = 0
        self.nullable = True
        self.index = -1
        self.type_table = None

    def kind(self) -> str:
        base = TYPE_NAMES.get(self.type_id, "type%d" % self.type_id)
        if self.bit_width and self.type_id == T_INT:
            return "int%d" % self.bit_width
        return base

    def __repr__(self):
        return "Field(%s:%s%s)" % (self.name, self.kind(),
                                   " dict" if self.dictionary_id is not None else "")


class FeatherFile:
    def __init__(self, path: str):
        self.path = path
        # memory-map instead of reading the whole file: the MaleCNS edge list is 1 GB
        # and decoding it column by column keeps peak RSS low.
        self._fh = open(path, "rb")
        try:
            import mmap
            self.data = mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_READ)
        except Exception:
            self.data = self._fh.read()
        if self.data[:6] != b"ARROW1":
            raise ValueError("not an Arrow IPC file: %s" % path)
        if self.data[-6:] != b"ARROW1":
            raise ValueError("truncated Arrow file (no trailing magic)")
        footer_len = struct.unpack_from("<i", self.data, len(self.data) - 10)[0]
        self.footer = Table(self.data, len(self.data) - 10 - footer_len)
        self.schema_msg, _ = self._message_at(8)
        self.record_batches: list[tuple[int, int]] = []
        n = self.footer.vector_len(3)          # Footer.recordBatches: vector<Block>
        for i in range(n):
            offset = self.footer.vector_struct_i64(3, i, 24, 0)
            meta_len = self.footer.vector_struct_i32(3, i, 24, 8)
            if meta_len:
                self.record_batches.append((offset, meta_len))
        self.fields = self._parse_schema()
        self._dictionaries = None

    # ---------------------------------------------------------------- messages
    def _frame(self, offset: int):
        """Locate one message frame: (root uoffset position, meta length).

        Arrow's file layout starts with "ARROW1\\0\\0" (8 bytes), so the first frame
        begins at offset 8 -- not at 0.  Each frame is `0xFFFFFFFF` + int32 length
        (current writers) or a bare int32 length (legacy), followed by the message
        flatbuffer whose *root uoffset* sits right after the length.
        """
        first = struct.unpack_from("<I", self.data, offset)[0]
        if first == 0xFFFFFFFF:
            return offset + 8, struct.unpack_from("<i", self.data, offset + 4)[0]
        return offset + 4, struct.unpack_from("<i", self.data, offset)[0]

    def _message_at(self, offset: int):
        """Return (Message root Table, body start offset) for the frame at `offset`."""
        root_at, meta_len = self._frame(offset)
        return Table(self.data, root_at), root_at + meta_len

    # Message: 0 version, 1 header_type(union tag), 2 header(union value), 3 bodyLength
    def _message_header(self, msg: Table) -> Table | None:
        t = msg.table(2) or msg.table(1)
        return t

    def _parse_schema(self) -> list[Field]:
        sch = self._message_header(self.schema_msg)
        if sch is None:
            raise ValueError("no Schema table in the Arrow file header")
        # Column names come from the schema; the Arrow *type* comes from the pandas
        # metadata JSON, because walking the Type sub-table is brittle across pyarrow
        # versions while the pandas blob states every column's dtype explicitly.
        # Child vectors are not walked: nothing this project reads uses nested columns.
        pandas_types = self._pandas_column_types()
        fields = []
        for i in range(sch.vector_len(1)):      # Schema.fields
            ft = sch.vector_table(1, i)
            if ft is None:
                continue
            f = Field()
            f.name = ft.string(0) or ""
            f.nullable = ft.bool_(1, True)
            # The union *tag* is the authoritative Arrow type id; the union *value* is a
            # table holding that type's parameters (bitWidth for Int, precision for
            # FloatingPoint, children for List, ...).  Reading a type id out of the
            # parameter table is wrong -- for Int the first slot is the bit width, so
            # `i8(0)` returns 64 and the column is mistaken for an unknown type.
            tag_at = ft._slot(2)
            f.type_id = self.data[tag_at] if tag_at is not None else T_NONE
            f.type_table = self._type_table(ft) if f.type_id in TYPE_NAMES else None
            if f.type_id == T_INT and f.type_table is not None:
                # only accept widths Arrow actually defines; anything else means the
                # union value slot pointed at unrelated bytes
                bw = f.type_table.i32(0, 0)
                if bw in (8, 16, 32, 64):
                    f.bit_width = bw
            # DictionaryEncoding is Field field 4; its presence is the reliable signal
            # that a column is dictionary-encoded.  Its layout is
            # 0 id(int64), 1 indexType(Int), 2 isOrdered(bool) -- the *index* width we
            # need for decoding lives in the nested Int table, not in the encoding table.
            dict_table = ft.table(4)
            if dict_table is not None:
                f.dictionary_id = dict_table.i64(0)
                index_type = dict_table.table(1)
                if index_type is not None:
                    bw = index_type.i32(0, 0)
                    if bw in (8, 16, 32, 64):
                        f.bit_width = bw
            key = f.name.split(".")[-1]
            kind = pandas_types.get(key)
            # pandas metadata as a fallback / cross-check for the physical type
            if f.type_id not in TYPE_NAMES and f.dictionary_id is None:
                if kind in ("int8", "int16", "int32", "int64"):
                    f.type_id, f.bit_width = T_INT, int(kind[3:])
                elif kind in ("float32", "float64", "double"):
                    f.type_id = T_FLOATINGPOINT
                elif kind == "bool":
                    f.type_id = T_BOOL
                elif kind and kind.startswith("list"):
                    f.type_id = T_LIST
                    child = Field()
                    child.name = f.name + ".item"
                    child.type_id = T_INT
                    child.bit_width = 64
                    f.children.append(child)
                else:
                    f.type_id = T_UTF8
            # A dictionary-encoded column still carries an Arrow *value* type (utf8 for
            # every text column here); trust it, and only fall back to the metadata when
            # the union tag was unreadable.
            if f.dictionary_id is not None and f.type_id not in TYPE_NAMES:
                f.type_id = T_UTF8
            if f.type_id == T_LIST and not f.children:
                child = Field()
                child.name = f.name + ".item"
                child.type_id = T_INT
                child.bit_width = 64
                f.children.append(child)
            if f.type_id == T_INT and not f.bit_width:
                f.bit_width = int((kind or "int32")[3:]) if kind and kind.startswith("int") else 32
            f.index = len(fields)
            fields.append(f)
        return fields

    @staticmethod
    def _type_table(ft: Table) -> "Table | None":
        """Locate the arrow Type sub-table of a Field.

        The Arrow `Type` union is Field field 3, and flatbuffers stores a union as a
        two-slot pair: an int8 tag at field slot 2 followed by the uoffset value at slot
        3.  Reading the *tag* slot as if it were an offset lands anywhere in the file
        (the tag is a small integer such as 2 or 5, so `table(2)` dereferences to
        whatever byte sits a few bytes further on) and yields junk.

        This table holds only the type's *parameters*; the type itself comes from the
        tag, which the caller reads.  A previous version probed slots (2, 5, 1) for
        "something that looks like an arrow type", which mistyped whole columns.
        """
        t = ft.table(3)
        if t is None:
            return None
        # A flatbuffer table's soffset points *backwards* to its vtable.  Tables that
        # reuse an earlier, larger vtable are normal (pyarrow emits one vtable per type
        # kind), so the only structural check worth making is that the vtable lies inside
        # the buffer and has a plausible length.
        if not (0 <= t.vtable < len(t.buf)) or t.vlen < 4 or t.vlen % 2:
            return None
        return t

    def _pandas_column_types(self) -> dict:
        """Read the pandas metadata blob pyarrow embeds -> {column: numpy dtype}."""
        import json as _json
        try:
            head = bytes(self.data[:1 << 20])
            start = head.find(b'{"index_columns"')
            if start < 0:
                return {}
            text = head[start:].decode("utf-8", "replace")
            meta, _end = _json.JSONDecoder().raw_decode(text)
        except Exception:
            return {}
        out = {}
        for c in meta.get("columns", []):
            out[c.get("name")] = c.get("numpy_type") or c.get("pandas_type")
        return out

    def _parse_field(self, ft: Table, depth: int = 0) -> Field:
        f = Field()
        f.name = ft.string(0) or ""
        f.nullable = ft.bool_(1, True)
        f.type_table = ft.table(2)
        if f.type_table is not None:
            f.type_id = f.type_table.i8(0)
        if f.type_table is None or f.type_id not in TYPE_NAMES:
            # The Type union value's location varies between writers; find the arrow
            # type id near the field table instead of failing outright.
            for probe in range(max(0, ft.pos + 1), min(len(ft.buf), ft.pos + 32)):
                tid = ft.buf[probe]
                if tid in TYPE_NAMES:
                    f.type_id = tid
                    break
        dict_table = ft.table(4)
        if dict_table is not None:
            f.dictionary_id = dict_table.i64(0)
        if depth < 6:
            for i in range(ft.vector_len(3)):       # Field.children
                child = ft.vector_table(3, i)
                if child is not None:
                    f.children.append(self._parse_field(child, depth + 1))
        if f.type_table is not None:
            if f.type_id == T_INT:
                f.bit_width = f.type_table.i32(1, 32)
            elif f.type_id in (T_FIXED_SIZE_BINARY, T_FIXED_SIZE_LIST):
                f.byte_width = f.type_table.i32(1, 0)
            elif f.type_id == T_DECIMAL:
                f.byte_width = f.type_table.i32(2, 16)
        return f

    # ---------------------------------------------------------------- schema text
    def schema_summary(self) -> str:
        out = []
        for f in self.fields:
            kind = f.kind()
            if f.type_id == T_LIST and f.children:
                kind = "list<%s>" % f.children[0].kind()
            out.append("%s:%s%s" % (f.name, kind, " (dict)" if f.dictionary_id is not None else ""))
        return ", ".join(out)

    # ---------------------------------------------------------------- batches
    def iter_batches(self) -> Iterator[dict]:
        dicts = self._collect_dictionaries()
        for offset, _meta_len in self.record_batches:
            msg, body_start = self._message_at(offset)
            rb = msg.table(2) or msg.table(1)     # Message.recordBatch
            if rb is None:
                continue
            yield self._read_batch(rb, body_start, dicts)

    def read_all(self, columns: list[str] | None = None) -> dict:
        want = set(columns) if columns else None
        out: dict = {}
        for batch in self.iter_batches():
            for name, values in batch.items():
                if want is not None and name not in want:
                    continue
                out.setdefault(name, []).extend(values)
        return out

    def _read_batch(self, batch: Table, body_start: int, dicts: dict,
                    strict: bool = True) -> dict:
        # RecordBatch fields: 0 length, 1 nodes (vector<FieldNode>, inline structs of
        # 16 bytes), 2 buffers (vector<Buffer>, inline structs of 16 bytes),
        # 3 compression, 4 variadicBufferCounts.  Nodes/buffers are *structs*, so they
        # are read in place rather than dereferenced as tables.
        n_nodes = batch.vector_len(1)
        n_buffers = batch.vector_len(2)
        # `strict` is off while decoding a DictionaryBatch: that payload is a one-column
        # pseudo-batch, so it has a single FieldNode and far fewer buffers than the file's
        # full schema would demand.
        if strict and len(self.fields) and (n_nodes < len(self.fields)
                                            or n_buffers < 2 * len(self.fields)):
            raise ValueError("not a record batch (nodes=%d, buffers=%d, fields=%d)"
                             % (n_nodes, n_buffers, len(self.fields)))
        nodes = [batch.vector_struct_i64(1, i, 16, 0) for i in range(n_nodes)]
        buffers = [(batch.vector_struct_i64(2, i, 16, 0), batch.vector_struct_i64(2, i, 16, 8))
                   for i in range(n_buffers)]
        comp = batch.table(3)
        codec = comp.i8(0) if comp is not None else COMPRESSION_NONE
        node_i = [0]
        buf_i = [0]
        _TRACE = []
        _read_batch.trace = _TRACE

        def take_buffer() -> bytes:
            _TRACE.append((sys._getframe(1).f_lineno, buf_i[0], buffers[buf_i[0]]))
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1
            if ln == 0:
                return b""
            raw = bytes(self.data[body_start + off: body_start + off + ln])
            if codec != COMPRESSION_NONE and ln >= 8:
                declared = struct.unpack_from("<q", raw, 0)[0]
                return decompress(codec, raw[8:], declared)
            # Arrow buffers that are compressed are prefixed with an int64 holding the
            # uncompressed size; the codec field is not always filled in correctly, so
            # sniff the frame magic as well (pyarrow 19 writes LZ4_FRAME here).
            if ln >= 8:
                declared = struct.unpack_from("<q", raw, 0)[0]
                payload = raw[8:]
                if declared > 0 and len(payload) <= declared:
                    if payload[:4] == bytes.fromhex("04224d18"):
                        return _lz4_frame(payload)
                    if payload[:4] == bytes.fromhex("28b52ffd"):
                        from compression import zstd
                        return zstd.decompress(payload)
                    if payload[:2] == b"\x1f\x8b":
                        import gzip
                        return gzip.decompress(payload)
            return raw

        def _decode_values(fld: Field, count: int):
            """Decode one primitive buffer set; used for list children too.

            Defined before `decode` uses it: a nested `def` only binds its name when the
            enclosing function body executes that statement, so keeping it below the
            `T_LIST` branch left the list path raising UnboundLocalError.
            """
            if fld.type_id == T_INT:
                return _decode_ints(take_buffer(), fld.bit_width or 32, count)
            if fld.type_id == T_FLOATINGPOINT:
                buf = take_buffer()
                width = fld.type_table.i32(0, 2) if fld.type_table else 2
                if width == 1:
                    return list(struct.unpack_from("<%df" % count, buf, 0)) if count else []
                return list(struct.unpack_from("<%dd" % count, buf, 0)) if count else []
            if fld.type_id == T_BOOL:
                buf = take_buffer()
                return [bool((buf[i >> 3] >> (i & 7)) & 1) for i in range(count)]
            return []

        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1
            take_buffer()          # validity bitmap (nulls are not tracked here)

            if field.dictionary_id is not None:
                idx_buf = take_buffer()
                bw = field.bit_width or 32
                # dictionary indices are bit-packed: derive the width from the buffer
                # when the schema did not give us one (n * bw / 8 bytes expected)
                if n and len(idx_buf) < (bw * n + 7) // 8:
                    for cand in (1, 2, 4, 8, 16, 32, 64):
                        if len(idx_buf) >= (cand * n + 7) // 8:
                            bw = cand
                if bw in (1, 2, 4):
                    idxs = _decode_bitpacked(idx_buf, bw, n)
                else:
                    idxs = _decode_ints(idx_buf, bw, n)
                table = dicts.get(field.dictionary_id)
                if table is None:
                    # No dictionary was collected (a file may keep its dictionaries after
                    # the data, which this reader does not scan): fall back to the raw
                    # indices so the column still lines up positionally rather than
                    # silently returning decoded-looking text.
                    return idxs
                return [table[i] if 0 <= i < len(table) else None for i in idxs]

            t = field.type_id
            if t == T_INT:
                return _decode_ints(take_buffer(), field.bit_width or 32, n)
            if t == T_FLOATINGPOINT:
                buf = take_buffer()
                width = field.type_table.i32(0, 2) if field.type_table else 2
                if width == 1:
                    return list(struct.unpack_from("<%df" % n, buf, 0)) if n else []
                return list(struct.unpack_from("<%dd" % n, buf, 0)) if n else []
            if t == T_BOOL:
                buf = take_buffer()
                return [bool((buf[i >> 3] >> (i & 7)) & 1) for i in range(n)]
            if t in (T_UTF8, T_BINARY, T_LARGE_UTF8, T_LARGE_BINARY):
                offsets_buf = take_buffer()
                data_buf = take_buffer()
                wide = t in (T_LARGE_UTF8, T_LARGE_BINARY)
                offsets = struct.unpack_from("<%d%s" % (n + 1, "q" if wide else "i"),
                                             offsets_buf, 0)
                raw = [data_buf[offsets[i]:offsets[i + 1]] for i in range(n)]
                if t in (T_UTF8, T_LARGE_UTF8):
                    return [v.decode("utf-8", "replace") for v in raw]
                return raw
            if t in (T_LIST, T_LARGE_LIST):
                wide = t == T_LARGE_LIST
                # A list column contributes *two* buffers of its own -- validity then
                # offsets -- and the child's buffers follow after them.  Skipping the
                # validity bitmap here desynchronises every later column and reads the
                # child's data buffer as if it were the offsets.
                take_buffer()          # validity bitmap
                offsets_buf = take_buffer()
                if len(offsets_buf) < struct.calcsize("<%d%s" % (n + 1, "q" if wide else "i")):
                    # fall back to whichever offset width the buffer actually holds
                    if len(offsets_buf) >= 8 * (n + 1):
                        wide = True
                    elif len(offsets_buf) >= 4 * (n + 1):
                        wide = False
                fmt = "<%d%s" % (n + 1, "q" if wide else "i")
                offsets = struct.unpack_from(fmt, offsets_buf, 0)
                child = field.children[0] if field.children else None
                if child is None:
                    # consume the child's node + buffers so later fields stay aligned
                    node_i[0] += 1
                    take_buffer()
                    take_buffer()
                    return [[] for _ in range(n)]
                # the child column has its own FieldNode: its length is the element count
                child_vals = _decode_values(child, nodes[node_i[0]])
                node_i[0] += 1
                take_buffer()          # child validity bitmap
                take_buffer()          # child data
                return [child_vals[offsets[i]:offsets[i + 1]] for i in range(n)]

            if t == T_STRUCT:
                return {c.name: decode(c) for c in field.children}
            raise ValueError("unsupported Arrow type %s for field %s" % (t, field.name))

        out = {}
        for field in self.fields:
            out[field.name] = decode(field)
            if hasattr(self, "_on_column"):
                self._on_column(field.name)
        return out

    # ---------------------------------------------------------------- dictionaries
    def _collect_dictionaries(self) -> dict:
        """Read every DictionaryBatch that precedes the first RecordBatch.

        DictionaryBatch messages are emitted up front, one per dictionary-encoded column,
        and their payload is a *dictionary* (an array of the distinct values), not a page
        of the column.  The scan has to key off the right Message header tags or it will
        try to decode the Schema message as a dictionary and stop at the first
        DictionaryBatch as if it were the end of the metadata.
        """
        if self._dictionaries is not None:
            return self._dictionaries
        dicts: dict = {}
        pos = 8
        end = len(self.data) - 10
        while pos < end:
            msg, body_start = self._message_at(pos)
            mtype = msg.i8(1, 0)             # Message.header_type
            body_len = msg.i64(3, 0)
            if mtype == MSG_RECORD_BATCH:    # data starts here -> no more dictionaries
                break
            if mtype == MSG_DICTIONARY_BATCH:
                # DictionaryBatch: 0 id(int64), 1 data(RecordBatch), 2 isDelta(bool)
                db = msg.table(2) or msg.table(1)
                if db is not None:
                    dict_id = db.i64(0)
                    values = self._read_dict_values(db.table(1), body_start, dict_id)
                    if values:
                        # A delta batch appends to the dictionary already collected
                        # rather than replacing it.
                        dicts.setdefault(dict_id, []).extend(values)
            pos = body_start + body_len
        self._dictionaries = dicts
        return dicts

    def _field_for_dictionary(self, dict_id: int) -> "Field":
        """The schema field carrying the dictionary with this id.

        The dictionary's *value* type is the Arrow type of the field that references it
        -- for these tables that is always utf8, so the values are the usual
        validity/offsets/data triple of a string array.  The id is looked up rather than
        guessed, because a file may dictionary-encode columns of different types and
        decoding with the wrong one consumes the wrong number of buffers.
        """
        for f in self.fields:
            if f.dictionary_id == dict_id:
                return f
        return next((f for f in self.fields if f.dictionary_id is not None), None)

    def _read_dict_values(self, batch: Table | None, body_start: int, dict_id: int = 0):
        """Decode a DictionaryBatch's `data` RecordBatch into a list of values.

        The batch holds exactly one column -- the dictionary -- and its buffers are laid
        out relative to this message's body, exactly like a normal record batch column.
        """
        if batch is None:
            return []
        value_field = self._field_for_dictionary(dict_id)
        if value_field is None:
            return []
        # Reuse the ordinary column decoder by presenting the dictionary as a
        # single-column schema.
        physical = Field()
        physical.name = value_field.name
        physical.type_id = value_field.type_id
        physical.type_table = value_field.type_table
        physical.bit_width = value_field.bit_width
        saver = self.fields
        self.fields = [physical]
        try:
            # strict=False: the "at least 2 buffers per field" sanity check in
            # `_read_batch` applies to a full record batch, and a one-column dictionary
            # legitimately has a single FieldNode.
            batch_dict = self._read_batch(batch, body_start, {}, strict=False)
            return batch_dict.get(physical.name, [])
        finally:
            self.fields = saver


def _decode_bitpacked(buf: bytes, bit_width: int, n: int) -> list:
    """LSB-first bit-packed integers, as used for Arrow dictionary indices."""
    out = []
    if bit_width == 1:
        for i in range(n):
            out.append((buf[i >> 3] >> (i & 7)) & 1)
        return out
    mask = (1 << bit_width) - 1
    acc = 0
    bits = 0
    pos = 0
    for _ in range(n):
        while bits < bit_width:
            acc |= buf[pos] << bits
            pos += 1
            bits += 8
        out.append(acc & mask)
        acc >>= bit_width
        bits -= bit_width
    return out


def _decode_ints(buf: bytes, bit_width: int, n: int) -> list:
    if n == 0:
        return []
    need = {8: 1, 16: 2, 32: 4, 64: 8}[bit_width] * n
    if len(buf) < need:
        raise ValueError("int buffer too small: have %d bytes, need %d for %d x int%d"
                         % (len(buf), need, n, bit_width))
    if bit_width == 64:
        return list(struct.unpack_from("<%dq" % n, buf, 0))
    if bit_width == 32:
        return list(struct.unpack_from("<%di" % n, buf, 0))
    if bit_width == 16:
        return list(struct.unpack_from("<%dh" % n, buf, 0))
    if bit_width == 8:
        return list(struct.unpack_from("<%db" % n, buf, 0))
    raise ValueError("unsupported int width %d" % bit_width)


if False:
    import sys
    f = FeatherFile(sys.argv[1])
    print("fields:", f.schema_summary())
    print("record batches:", len(f.record_batches))
    for batch in f.iter_batches():
        for k, v in batch.items():
            print("  %-24s %d values  first=%s" % (k, len(v), v[:3]))
        break



