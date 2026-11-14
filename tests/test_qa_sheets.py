"""tools/qa_sheets.py: a partly typed page is dropped for its complete version, even when the complete page adds
too little ink to pass the --changed dedup, and a new page is never taken for a partial one."""
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import qa_sheets  # noqa: E402

W, H = 200, 8


def img(ink):
    """A dark box filling the frame, with white pixels at the (x, y) cells of `ink`."""
    rows = [bytearray(b"\x00\x00\x00" * W) for _ in range(H)]
    for x, y in ink:
        rows[y][3 * x:3 * x + 3] = b"\xff\xff\xff"
    return (W, H, 3, rows)


TEXT = {(x, 3) for x in range(0, 160, 4)}       # a line of "glyphs" (sparse ink: box rows stay mostly dark)
TYPED = {(x, 3) for x in range(0, 80, 4)}       # the same line half typed
CURSOR = {(82, y) for y in range(2, 6)}         # typing cursor after the partial text
OTHER = {(x + 2, 3) for x in range(0, 160, 4)}  # a different page on the same row


class PartialOf(unittest.TestCase):
    def test_more_ink_is_partial(self):
        self.assertTrue(qa_sheets.partial_of(img(TYPED), img(TEXT)))

    def test_cursor_gone_is_still_partial(self):
        self.assertTrue(qa_sheets.partial_of(img(TYPED | CURSOR), img(TEXT)))

    def test_new_page_is_not_partial(self):
        self.assertFalse(qa_sheets.partial_of(img(TEXT), img(OTHER)))
        self.assertFalse(qa_sheets.partial_of(img(TEXT), img(TEXT)))


class Frames(unittest.TestCase):
    def test_complete_page_kept_when_change_is_small(self):
        shots = [img(TYPED), img(TYPED | {(80, 3)}), img(OTHER)]
        real = qa_sheets.sheet.read_png
        qa_sheets.sheet.read_png = lambda p: shots[int(p.stem.split("_")[-1])]

        class D:
            def __truediv__(self, n):
                return Path("page_0")

            def glob(self, pat):
                return [Path("page_1"), Path("page_2")]
        try:
            with unittest.mock.patch.object(Path, "exists", lambda self: True):
                kept = qa_sheets.frames(D(), 0.01)
        finally:
            qa_sheets.sheet.read_png = real
        self.assertEqual(kept[0][3][3][3 * 80:3 * 81], b"\xff\xff\xff")   # the complete page, not the partial
        self.assertEqual(len(kept), 2)


if __name__ == "__main__":
    unittest.main()
