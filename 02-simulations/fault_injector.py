import argparse
import csv
import json
import os
import random
import time
import traceback
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional
import base64
import html

# ------------------------------
# Example target function (replace with your real function)
# ------------------------------
def process_packet(pkt_bytes: bytes) -> int:
    """Example defensive packet processor:
    - rejects None
    - enforces minimum length
    - rejects obvious non-printable corruption
    - returns checksum-like integer if valid
    """
    if pkt_bytes is None:
        raise ValueError("pkt_bytes is None")
    if len(pkt_bytes) < 20:
        raise ValueError("too short")

    # Reject obvious non-printable corruption:
    # (Adjust printable range to match your protocol if needed)
    if any(b < 32 or b > 126 for b in pkt_bytes):
        raise ValueError("non-printable byte detected")

    # existing checksum-like processing
    s = 0
    for b in pkt_bytes:
        s = (s + b) & 0xFFFF
        if (s & 0xFF) == 0x7E:
            s ^= 0xA5A5
    return s

# ------------------------------
# Fault models (same as earlier, slightly extended)
# ------------------------------
def flip_bits_in_bytes(data: bytes, num_bits: int, rng: random.Random) -> bytes:
    if data is None:
        return None
    ba = bytearray(data)
    if not ba:
        return bytes(ba)
    n = len(ba) * 8
    for _ in range(num_bits):
        bit = rng.randrange(n)
        idx = bit // 8
        bitpos = bit % 8
        ba[idx] ^= (1 << bitpos)
    return bytes(ba)

def stuck_at_value(data: bytes, idx: int, value: int) -> bytes:
    if data is None:
        return None
    ba = bytearray(data)
    if 0 <= idx < len(ba):
        ba[idx] = value & 0xFF
    return bytes(ba)

def corrupt_range(data: bytes, start: int, length: int, rng: random.Random) -> bytes:
    if data is None:
        return None
    ba = bytearray(data)
    for i in range(start, min(len(ba), start + length)):
        ba[i] = rng.randrange(256)
    return bytes(ba)

# ------------------------------
# Injection spec & results
# ------------------------------
@dataclass
class InjectionSpec:
    name: str
    kind: str  # 'bitflip', 'stuck', 'corrupt', 'delay', 'exception', 'null'
    params: Dict[str, Any]

@dataclass
class TrialResult:
    seed: int
    spec_name: str
    outcome: str  # 'pass','incorrect','exception'
    output: Optional[Any]
    baseline: Optional[Any]
    exception: Optional[str]
    mutated_input_b64: Optional[str]

# ------------------------------
# Harness
# ------------------------------
class FaultInjector:
    def __init__(self, target_fn: Callable[[bytes], Any], baseline_input: bytes, rng_seed: int):
        self.target_fn = target_fn
        self.baseline_input = baseline_input
        self.rng_seed = rng_seed
        self.rng_base = random.Random(rng_seed)

    def run_baseline(self, runs: int = 5) -> Any:
        outs = []
        for _ in range(runs):
            outs.append(self.target_fn(self.baseline_input))
        # simple check: all equal?
        if all(o == outs[0] for o in outs):
            return outs[0]
        # otherwise return the first and warn
        print("Warning: baseline outputs varied; using first result as baseline")
        return outs[0]

    def apply_injection(self, data: bytes, spec: InjectionSpec, rng: random.Random) -> Optional[bytes]:
        if spec.kind == "bitflip":
            return flip_bits_in_bytes(data, spec.params.get("num_bits", 1), rng)
        elif spec.kind == "stuck":
            return stuck_at_value(data, spec.params.get("idx", 0), spec.params.get("value", 0))
        elif spec.kind == "corrupt":
            return corrupt_range(data, spec.params.get("start", 0), spec.params.get("length", 1), rng)
        elif spec.kind == "null":
            return None
        elif spec.kind == "delay":
            # no mutation; caller will sleep
            return data
        elif spec.kind == "exception":
            raise RuntimeError("injected exception")
        else:
            return data

    def run_trials(self,
                   specs: List[InjectionSpec],
                   trials_per_spec: int,
                   outdir: str) -> List[TrialResult]:
        os.makedirs(outdir, exist_ok=True)
        baseline_out = self.run_baseline()
        csv_rows = []
        results: List[TrialResult] = []

        for spec in specs:
            for _ in range(trials_per_spec):
                seed = self.rng_base.randrange(2**30)
                rng = random.Random(seed)
                mutated_b64 = None
                try:
                    injected_input = self.apply_injection(self.baseline_input, spec, rng)
                    if spec.kind == "delay":
                        time.sleep(spec.params.get("delay_s", 0.01))

                    out = self.target_fn(injected_input)
                    if out == baseline_out:
                        outcome = "pass"
                    else:
                        outcome = "incorrect"
                    exc_text = None
                    # if incorrect or exception, save mutated input
                    if outcome != "pass":
                        mutated_b64 = None if injected_input is None else base64.b64encode(injected_input).decode()
                        if mutated_b64:
                            fname = f"{spec.name.replace(' ','_')}_seed_{seed}.bin"
                            path = os.path.join(outdir, "examples")
                            os.makedirs(path, exist_ok=True)
                            with open(os.path.join(path, fname), "wb") as fh:
                                fh.write(injected_input)
                except Exception as e:
                    outcome = "exception"
                    out = None
                    exc_text = traceback.format_exc()
                    mutated_b64 = None
                row = {
                    "seed": seed,
                    "spec": spec.name,
                    "kind": spec.kind,
                    "outcome": outcome,
                    "output": str(out),
                    "baseline": str(baseline_out),
                    "exception": exc_text,
                    "mutated_input_b64": mutated_b64
                }
                csv_rows.append(row)
                results.append(TrialResult(seed=seed, spec_name=spec.name, outcome=outcome, output=out,
                                           baseline=baseline_out, exception=exc_text,
                                           mutated_input_b64=mutated_b64))
        # write CSV
        csv_path = os.path.join(outdir, "results.csv")
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(csv_rows[0].keys()) if csv_rows else
                                    ["seed","spec","kind","outcome","output","baseline","exception","mutated_input_b64"])
            writer.writeheader()
            for r in csv_rows:
                writer.writerow(r)

        # write summary HTML
        self._write_html_summary(results, outdir)
        return results

    def _write_html_summary(self, results: List[TrialResult], outdir: str):
        by_spec = {}
        for r in results:
            s = r.spec_name
            by_spec.setdefault(s, {"total":0,"pass":0,"incorrect":0,"exception":0,"examples":[]})
            by_spec[s]["total"] += 1
            by_spec[s][r.outcome] += 1
            if r.outcome != "pass" and len(by_spec[s]["examples"]) < 5:
                by_spec[s]["examples"].append({
                    "seed": r.seed,
                    "outcome": r.outcome,
                    "exception": r.exception,
                    "mutated_input_b64": r.mutated_input_b64
                })
        html_parts = ["<html><head><meta charset='utf-8'><title>FI Summary</title></head><body>"]
        html_parts.append("<h1>Fault Injection Summary</h1>")
        html_parts.append("<table border='1' cellpadding='6'><tr><th>Spec</th><th>Total</th><th>Pass</th><th>Incorrect</th><th>Exception</th></tr>")
        for spec, data in by_spec.items():
            html_parts.append(f"<tr><td>{html.escape(spec)}</td><td>{data['total']}</td><td>{data['pass']}</td>"
                              f"<td>{data['incorrect']}</td><td>{data['exception']}</td></tr>")
        html_parts.append("</table><h2>Examples (up to 5 per spec)</h2>")
        for spec, data in by_spec.items():
            html_parts.append(f"<h3>{html.escape(spec)}</h3><ul>")
            for ex in data["examples"]:
                seed = ex["seed"]
                outcome = ex["outcome"]
                exc = html.escape(ex["exception"] or "")
                b64 = ex.get("mutated_input_b64") or ""
                snippet = (b64[:120] + "...") if b64 else ""
                html_parts.append(f"<li>seed={seed} outcome={outcome} exception={exc} input_b64={snippet}</li>")
            html_parts.append("</ul>")
        html_parts.append("</body></html>")
        with open(os.path.join(outdir, "summary.html"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(html_parts))

# ------------------------------
# Defaults & specs
# ------------------------------
DEFAULT_SPECS = [
    InjectionSpec(name="1-bit-flip", kind="bitflip", params={"num_bits": 1}),
    InjectionSpec(name="2-bit-flip", kind="bitflip", params={"num_bits": 2}),
    InjectionSpec(name="stuck-zero-at-5", kind="stuck", params={"idx": 5, "value": 0}),
    InjectionSpec(name="corrupt-range-3", kind="corrupt", params={"start": 3, "length": 4}),
    InjectionSpec(name="null-input", kind="null", params={}),
    InjectionSpec(name="timing-delay", kind="delay", params={"delay_s": 0.005}),
    InjectionSpec(name="forced-exception", kind="exception", params={}),
]

# ------------------------------
# CLI
# ------------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", default="reports", help="output directory")
    p.add_argument("--trials", type=int, default=100, help="trials per spec")
    p.add_argument("--seed", type=int, default=None, help="master RNG seed (default random)")
    p.add_argument("--reproduce", action="store_true", help="reproduce a single trial by seed & spec")
    p.add_argument("--spec", type=str, default=None, help="spec name used with --reproduce")
    p.add_argument("--trial-seed", type=int, default=None, help="seed to reproduce (used with --reproduce)")
    return p.parse_args()

def reproduce_single(target_fn, baseline_input, seed:int, spec_name:str, outdir:str):
    # Find matching spec
    spec = next((s for s in DEFAULT_SPECS if s.name == spec_name), None)
    if not spec:
        raise ValueError("Spec not found: " + spec_name)
    injector = FaultInjector(target_fn, baseline_input, rng_seed=seed)  # seed used for reproducible RNG base
    # We will directly apply injection once using the seed
    rng = random.Random(seed)
    injected = injector.apply_injection(baseline_input, spec, rng)
    print("Reproducing spec:", spec_name, "seed:", seed)
    print("Mutated input (base64):", "" if injected is None else base64.b64encode(injected).decode())
    out = None
    try:
        out = target_fn(injected)
        print("Output:", out)
    except Exception:
        print("Exception while running target:")
        print(traceback.format_exc())
    # Save mutated input
    path = os.path.join(outdir, "reproductions")
    os.makedirs(path, exist_ok=True)
    if injected is not None:
        with open(os.path.join(path, f"{spec_name}_seed_{seed}.bin"), "wb") as fh:
            fh.write(injected)

def main():
    args = parse_args()
    master_seed = args.seed if args.seed is not None else random.randrange(2**30)
    baseline = b"Hello, this is baseline data 1234567890"
    if args.reproduce:
        if args.spec is None or args.trial_seed is None:
            raise SystemExit("For --reproduce you must provide --spec and --trial-seed")
        reproduce_single(process_packet, baseline, args.trial_seed, args.spec, args.outdir)
        return

    injector = FaultInjector(process_packet, baseline, master_seed)
    results = injector.run_trials(DEFAULT_SPECS, trials_per_spec=args.trials, outdir=args.outdir)
    print(f"Done. Results: {len(results)} trials. Reports in {args.outdir}")

if __name__ == "__main__":
    main()
