### Fault Injection Simulation — What I learned

This repo is my hands-on fault-injection playground. I used a small, reproducible harness to mutate a known-good input (bit flips, small corruptions, None, delays) and exercised my process_packet function to find silent corruptions. I reproduced failing cases deterministically, added defensive checks, turned failures into fixtures + pytest tests, and verified the fix.
---

## TL;DR 

I found a one-byte corruption that made my code return a wrong value silently, reproduced that exact corrupted input by seed, added a validation that rejects it, and locked the fix with a regression test.
---

## What I learned

**What fault injection is**: intentionally corrupting inputs to simulate hardware/transmission faults.

# How outcomes map to risk:
**pass** — mutated input produced the same output (good).
**incorrect** — mutated input produced a different output without an error (dangerous; needs action).
**exception** — mutated input raised an error (detectable; usually preferable).

* How to reproduce failures deterministically using RNG seeds the harness records.
* How to triage a failing seed: decode mutated bytes, inspect which byte(s) changed, decide a defensive fix.
* How to convert failing inputs into fixtures + pytest tests so the issue cannot silently reappear.
* How to run the harness in an isolated .venv to avoid unrelated pytest plugin issues.


## Repo layout

.
├─ README.md
├─ fault_injector.py                  # harness + example target (process_packet)
├─ reports/                           # harness outputs: results.csv, summary.html, reproductions/
├─ tests/
│  ├─ fixtures/                       # saved mutated inputs (binary fixtures)
│  └─ test_fi_repro.py                # manual reproducible test (example)
├─ tests/generated_fi_tests/          # auto-generated tests (from fixtures)
├─ tools/
│  ├─ extract_and_reproduce.py        # extracts seeds & reproduces binaries
│  ├─ generate_tests_from_fixtures.py # generates pytest files per fixture (includes sys.path shim)
│  └─ apply_defensive_patch.py        # (optional) inserts defensive checks into fault_injector.py
└─ .venv/                             # optional virtualenv for isolation
---

Quick start (commands I used)

> (recommended: run inside .venv so global packages/plugins don't interfere)

# create & activate venv (optional but recommended)
```bash
python -m venv .venv
source .venv/bin/activate
```

# install pytest (only needed for running tests)
```bash
pip install --upgrade pip
pip install pytest
```

# run the harness (100 trials per spec)
```bash
python3 fault_injector.py --outdir reports --trials 100 --seed 42
```

# open outputs:
# - reports/results.csv  (one row per trial)
# - reports/summary.html (per-spec summary)

---

## Full flow (what happens when I run the harness)

1. Baseline: harness computes the baseline output by running process_packet(baseline).
2. Mutate: for each spec (1-bit-flip, 2-bit-flip, corrupt-range, etc.) and trial, the harness mutates a copy of baseline (randomly using a seed).
3. Run: harness calls process_packet(mutated_input) and captures return value or exception.
4. Classify: outcome is pass (same as baseline), incorrect (different but no error), or exception (raised).
5. Record: harness writes a CSV row including seed, spec, outcome, output, baseline, and mutated_input_b64.
6. Reproduce: --reproduce --trial-seed <seed> regenerates the same mutated bytes and writes a binary to reports/reproductions/1-bit-flip_seed_<seed>.bin.
7. Triage & fix: inspect mutated bytes, add defensive checks or protocol-level integrity checks, save the reproduced binary as a fixture and write pytest that expects the input to be rejected.
8. Verify: re-run pytest and the harness to measure improvement.
---

## How I reproduced & triaged a failing case (concrete steps)

1. Find a row in reports/results.csv with outcome == incorrect. Copy the seed and spec.
2. Reproduce the exact mutated input:
```bash
python3 fault_injector.py --reproduce --spec "1-bit-flip" --trial-seed 239081663 --outdir reports
```
# output file -> reports/reproductions/1-bit-flip_seed_239081663.bin
3. Inspect the mutated binary:
```bash
xxd reports/reproductions/1-bit-flip_seed_239081663.bin | sed -n '1,4p'
```
or decode the base64 printed by the harness:
```bash
echo 'SGVsbG8sI...' | base64 --decode > mutated.bin
xxd mutated.bin
```
4. I found a single-byte flip (0x69 -> 0xE9) that changed the checksum-like output from 3134 → 3262.
5. I added defensive validation to process_packet to reject non-printable bytes and short messages, so the mutated input raises ValueError.
6. I saved the reproduced .bin into tests/fixtures/ and created a pytest asserting process_packet(mutated) raises.
---

## Example defensive code I used (put into fault_injector.py)
```python
def process_packet(pkt_bytes: bytes) -> int:
    if pkt_bytes is None:
        raise ValueError("pkt_bytes is None")
    if len(pkt_bytes) < 20:
        raise ValueError("too short")
    # Quick check: reject obvious non-printable corruption (adjust for your protocol)
    if any(b < 32 or b > 126 for b in pkt_bytes):
        raise ValueError("non-printable byte detected")
    # existing checksum-like logic...
    s = 0
    for b in pkt_bytes:
        s = (s + b) & 0xFFFF
        if (s & 0xFF) == 0x7E:
            s ^= 0xA5A5
    return s
```

> Note: printable-byte checks are a quick mitigation. For production, prefer protocol-aware validation (field lengths, value ranges, CRC/HMAC).
---

## Automating fixture extraction & test generation (tools)

I use the scripts in tools/:

tools/extract_and_reproduce.py
- Reads reports/results.csv and collects the top N incorrect seeds (first-occurrence order) and runs the harness --reproduce for each seed. It copies the reproduced binaries into tests/fixtures/.

tools/generate_tests_from_fixtures.py
- Scans tests/fixtures/ for 1-bit-flip_seed_*.bin entries and writes one pytest file per fixture into tests/generated_fi_tests/. Each generated test includes a sys.path shim so from fault_injector import process_packet works without tweaking PYTHONPATH.

tools/apply_defensive_patch.py (optional)
- Small helper that inserts the defensive validation into fault_injector.py if it’s not already present (it backups the original file).


##Example automation workflow I ran:

# extract and reproduce top 10 incorrect seeds
```bash
python3 tools/extract_and_reproduce.py --csv reports/results.csv --n 10 --outdir reports
```

# generate pytest files from the fixtures
```bash
python3 tools/generate_tests_from_fixtures.py
```

# (optionally) apply the defensive patch automatically
```bash
python3 tools/apply_defensive_patch.py
```

# run generated tests
```bash
pytest -q tests/generated_fi_tests
```
---

## How I interpret results (practical rubric)

- incorrect / total < ~2%: acceptable for now.
- incorrect / total 2–10%: moderate risk — prioritize validation on hot paths.
- incorrect / total > 10%: high risk — add checksums/HMACs and stronger validation.

*Goal: reduce incorrect counts (silent failures) — it's fine if exception counts increase (visible failures are better).*
---

## Troubleshooting & notes

If pytest errors with ModuleNotFoundError: No module named 'fault_injector', run tests with repo root on PYTHONPATH:
```bash
PYTHONPATH=. pytest -q tests/generated_fi_tests
```

or ensure tests include the small sys.path shim (the generator does this).

If pytest fails to import unrelated plugins, create a fresh virtualenv and install only pytest:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest

--reproduce prints mutated input as base64 — decode it if you prefer a binary file:

echo 'BASE64STRING' | base64 --decode > mutated.bin
```
---

## Next steps I will take

1. Use tools/extract_and_reproduce.py to collect and reproduce the top 20 incorrect seeds across specs.
2. Harden process_packet with protocol-aware validation (field checks, CRC/HMAC).
3. Add generated tests to CI and fail builds if regressions allow known corrupted inputs to be accepted.
4. Keep a fi-regressions/ document that lists seeds, their cause, and fix status.
---

## Appendix: default injection specs

* 1-bit-flip — flip one random bit.
* 2-bit-flip — flip two random bits.
* stuck-zero-at-5 — set byte at index 5 to 0.
* corrupt-range-3 — randomize 3 contiguous bytes.
* null-input — pass None.
* timing-delay — inject a small delay.
* forced-exception — harness forces an exception.
---