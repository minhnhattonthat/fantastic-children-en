"""writelog.py: every byte the build writes goes through one put(), which logs it for romdiff.py --writes.

    log = WriteLog(orig)                 # orig = the original dump (bytes past its end count as 0xFF)
    log.put(out, off, data, "pages")     # out[off:off+len(data)] = data, growing `out` with 0xFF as needed
    log.save(path)                       # `OFFSET ORIG_HEX NEW_HEX writer` per line (romdiff.py's --writes format)
    log.outside(ranges)                  # writes not inside any (first, last, why) range of tools/allowed.py

A put() with log=None (identity builds, tests) just writes; see put() below.
"""


class WriteLog:
    def __init__(self, orig):
        self.orig = bytes(orig)
        self.writes = []   # (off, orig bytes, new bytes, writer)

    def put(self, out, off, data, by):
        data = bytes(data)
        if not data:
            return
        end = off + len(data)
        if len(out) < end:
            out += b"\xFF" * (end - len(out))
        was = self.orig[off:end]
        was += b"\xFF" * (len(data) - len(was))
        out[off:end] = data
        self.writes.append((off, was, data, by))

    def save(self, path):
        path.parent.mkdir(exist_ok=True)
        path.write_text("".join(f"{o:X} {a.hex()} {b.hex()} {by}\n" for o, a, b, by in self.writes),
                        encoding="utf-8", newline="\n")
        return path

    def outside(self, ranges):
        """[(off, end, writer)] for writes not wholly inside one allowed range."""
        return [(o, o + len(b), by) for o, _, b, by in self.writes
                if not any(a <= o and o + len(b) - 1 <= z for a, z, _ in ranges)]


def put(out, off, data, by, log=None):
    """out[off:off+len(data)] = data (out grows with 0xFF), logged when a WriteLog is given."""
    if log is not None:
        log.put(out, off, data, by)
        return
    end = off + len(data)
    if len(out) < end:
        out += b"\xFF" * (end - len(out))
    out[off:end] = data
