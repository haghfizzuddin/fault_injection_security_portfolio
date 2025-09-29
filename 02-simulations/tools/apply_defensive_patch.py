#!/usr/bin/env python3
"""
tools/apply_defensive_patch.py

Insert defensive validation into the existing process_packet(...) function in fault_injector.py.
This is a minimal, safe insertion: it looks for the function header 'def process_packet('
and injects checks before the existing computation (before the 's = 0' assignment).
Backs up original to fault_injector.py.bak
"""
import re, sys, shutil, pathlib

SRC = pathlib.Path("fault_injector.py")
if not SRC.exists():
    print("fault_injector.py not found in repo root."); sys.exit(1)

bak = SRC.with_suffix(".py.bak")
shutil.copy2(SRC, bak)
text = SRC.read_text(encoding="utf-8")

# If already patched, skip
if "non-printable byte detected" in text:
    print("Defensive check already present; nothing to do.")
    sys.exit(0)

# Find the start of function def
m = re.search(r"def\s+process_packet\s*\(.*?\)\s*:\s*\n", text)
if not m:
    print("process_packet definition not found; aborting.")
    sys.exit(1)
start = m.end()

# Find insertion point: before first occurrence of a line that sets 's ='
ins_match = re.search(r"(^\s*s\s*=\s*0\s*$)", text[start:], flags=re.MULTILINE)
if not ins_match:
    # fallback: insert right after def header
    insert_pos = start
else:
    insert_pos = start + ins_match.start()

insertion = (
    "    # Defensive validation inserted by tools/apply_defensive_patch.py\n"
    "    if pkt_bytes is None:\n"
    "        raise ValueError(\"pkt_bytes is None\")\n"
    "    if len(pkt_bytes) < 20:\n"
    "        raise ValueError(\"too short\")\n"
    "    # Reject obvious non-printable corruption (adjust range per protocol)\n"
    "    if any(b < 32 or b > 126 for b in pkt_bytes):\n"
    "        raise ValueError(\"non-printable byte detected\")\n\n"
)

new_text = text[:insert_pos] + insertion + text[insert_pos:]
SRC.write_text(new_text, encoding="utf-8")
print("Patched fault_injector.py (backup at {})".format(bak))
