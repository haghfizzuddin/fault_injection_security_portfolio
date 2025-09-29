# tests/test_fi_repro.py
import sys, os
import pytest

# Ensure repo root is on sys.path so we can import modules at repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import the function under test from the module file at repo root.
# If you placed process_packet in a different file, change 'fault_injector' to that filename (no .py).
from fault_injector import process_packet

def test_reproduced_mutated_input_raises():
    fixture_path = "tests/fixtures/1-bit-flip_seed_239081663.bin"
    with open(fixture_path, "rb") as f:
        mutated = f.read()
    with pytest.raises(ValueError):
        process_packet(mutated)
