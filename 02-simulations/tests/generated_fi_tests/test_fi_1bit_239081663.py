import sys, os
# ensure repo root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from fault_injector import process_packet

def test_reproduced_239081663_raises():
    with open(r"tests/fixtures/1-bit-flip_seed_239081663.bin", "rb") as fh:
        mutated = fh.read()
    with pytest.raises(ValueError):
        process_packet(mutated)
