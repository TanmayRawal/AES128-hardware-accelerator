"""
assemble_report.py
Joins part1.tex through part5.tex into a single report.tex
"""
import os

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))

# Read all parts
parts = []
for i in range(1, 6):
    path = os.path.join(REPORT_DIR, f"part{i}.tex")
    with open(path, "r", encoding="utf-8") as f:
        parts.append(f.read())

# Part 1 has \begin{document} and title page but ends with \end{document}
# We need to:
#   - Strip \end{document} from part1
#   - Strip preamble+\begin{document} from parts 2-4
#   - Strip preamble+\begin{document} from part5, keep appendix content
#   - Add \end{document} at the very end

def strip_preamble(tex):
    """Remove everything up to and including \begin{document}"""
    marker = r"\begin{document}"
    idx = tex.find(marker)
    if idx != -1:
        return tex[idx + len(marker):]
    return tex

def strip_end_document(tex):
    """Remove \end{document} from the end"""
    return tex.replace(r"\end{document}", "").rstrip()

# Part 1: strip \end{document}
p1 = strip_end_document(parts[0])

# Parts 2-5: strip preamble AND strip \end{document}
p2 = strip_end_document(strip_preamble(parts[1]))
p3 = strip_end_document(strip_preamble(parts[2]))
p4 = strip_end_document(strip_preamble(parts[3]))
p5 = strip_end_document(strip_preamble(parts[4]))

# Assemble
final = p1 + "\n\n" + p2 + "\n\n" + p3 + "\n\n" + p4 + "\n\n" + p5 + "\n\n\\end{document}\n"

out_path = os.path.join(REPORT_DIR, "report.tex")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(final)

print(f"SUCCESS: report.tex assembled ({len(final)} chars, {final.count(chr(10))} lines)")
print(f"Output: {out_path}")
