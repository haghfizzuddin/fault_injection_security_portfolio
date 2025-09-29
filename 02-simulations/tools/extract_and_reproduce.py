import csv, subprocess, os, sys, argparse

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="reports/results.csv")
parser.add_argument("--spec", default="1-bit-flip")
parser.add_argument("--n", type=int, default=5)
parser.add_argument("--outdir", default="reports")
args = parser.parse_args()

if not os.path.exists(args.csv):
    print("CSV not found:", args.csv); sys.exit(1)

seeds = []
with open(args.csv, newline="") as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        if row.get("spec") == args.spec and row.get("outcome") == "incorrect":
            seeds.append(int(row.get("seed")))

seeds = seeds[:args.n]
print(f"Reproducing {len(seeds)} seeds for spec {args.spec}: {seeds}")

for s in seeds:
    cmd = ["python3", "fault_injector.py", "--reproduce", "--spec", args.spec, "--trial-seed", str(s), "--outdir", args.outdir]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
