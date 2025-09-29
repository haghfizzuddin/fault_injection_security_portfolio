#!/usr/bin/env python3
"""
tools/generate_tests_from_fixtures.py

Generate pytest test files in tests/generated_fi_tests/ for every binary fixture found in tests/fixtures/.
Each generated test asserts process_packet(mutated) raises ValueError.

Usage:
  python3 tools/generate_tests_from_fixtures.py
"""
import os, glob, textwrap
from pathlib import Path

FIX_DIR = Path("tests/fixtures")
OUT_DIR = Path("tests/generated_fi_tests")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADER = textwrap.dedent("""\
    import sys, os
    # ensure repo root is on sys.path
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    """)

TEMPLATE = textwrap.dedent("""\
    import pytest
    from fault_injector import process_packet

    def test_reproduced_{seed}_raises():
        with open(r"{fixture_path}", "rb") as fh:
            mutated = fh.read()
        with pytest.raises(ValueError):
            process_packet(mutated)
    """)

fixtures = sorted(FIX_DIR.glob("1-bit-flip_seed_*.bin"))
if not fixtures:
    print("No fixtures found in", FIX_DIR)
else:
    for f in fixtures:
        base = f.name
        seed = base.replace("1-bit-flip_seed_", "").replace(".bin", "")
        testname = f"test_fi_1bit_{seed}.py"
        fixture_path = str(f.as_posix())
        content = HEADER + TEMPLATE.format(seed=seed, fixture_path=fixture_path)
        out_path = OUT_DIR / testname
        out_path.write_text(content, encoding="utf-8")
        print("Wrote", out_path)
    print("Done — generated", len(fixtures), "tests in", OUT_DIR)
