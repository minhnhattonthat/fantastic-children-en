# Usage: bash tools/fl.sh bNNN  -- runs `tl.py fill bNNN` (full log in work/tl/fill.log) and prints
# the problems on one line ("id px/limit", glossary misses, BLANK = leading/trailing blank mismatch).
python -X utf8 tools/tl.py fill $1 > work/tl/fill.log 2>&1
sed -E "s/^  (p[0-9A-F]+): ([0-9]+) px > ([0-9]+) \(box (top|bottom)\): .*/\1 \2\/\3/; s/^  (p[0-9A-F]+): ([0-9]+ codes).*/\1 \2/; s/^  (p[0-9A-F]+): (glossary: [^:]*):.*/\1 \2/; s/^  (p[0-9A-F]+): leading.*/\1 BLANK/; s/^  (p[0-9A-F]+): (.{0,60}).*/\1 \2/" work/tl/fill.log | grep -v codes | paste -sd';'
