import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RomPinned(unittest.TestCase):
    def test_sha1_listing_matches_dump(self):
        line = (ROOT / "rom.sha1").read_text(encoding="utf-8").split("\n")
        entries = [l.split(None, 1) for l in line if l.strip() and not l.startswith("#")]
        self.assertEqual(len(entries), 1)
        want, name = entries[0]
        path = ROOT / name.strip().lstrip("*")
        if not path.is_file():
            self.skipTest("no ROM dump in rom/")
        self.assertEqual(hashlib.sha1(path.read_bytes()).hexdigest(), want)


if __name__ == "__main__":
    unittest.main()
