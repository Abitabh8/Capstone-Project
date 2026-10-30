#!/usr/bin/env python3
"""
sensitivity.py  --  Number-matching sensitivity analysis (Section 6.5 / 7.3)
Runs entirely in-process: no network, no ports, no real accounts.

It imports decide() from simulated_target.py UNCHANGED, and reproduces the
mock gateway's fixed-window rate limit and the event generator's Poisson
arrivals with the same seeds and run numbers as the main lab. It therefore
uses the same model and the same random sequences as run_lab.sh.

Usage (from the lab folder):
  python3 sensitivity.py --check lab_results.csv   # reproduce all 35 lab rows
  python3 sensitivity.py                           # write sensitivity_results.csv
"""
import argparse, csv, random
import simulated_target as T

CONDS = ["none", "rate_limiting", "context_rich", "number_matching", "combined"]
FREQS = [1, 2, 5, 10, 15, 20, 30]
DURATION_S = 15 * 60
RUNS_PER_CELL = 200
# (error multiplier, fatigue multiplier, prompts per window) -- as in mock_gateway.py
BASE = {"none": (1.00, 1.00, None), "rate_limiting": (1.00, 1.00, 3),
        "context_rich": (0.55, 0.85, None), "number_matching": (0.02, 1.00, None),
        "combined": (0.02, 0.85, 3)}
MULTIPLIERS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50]

def run_cell(cond, freq, err_mult=None, n=RUNS_PER_CELL):
    em, fm, cap = BASE[cond]
    if err_mult is not None: em = err_mult
    ci, fi = CONDS.index(cond), FREQS.index(freq)
    wins = []
    for k in range(n):
        rid = ci * 1400 + fi * 200 + k + 1          # same run numbers as event_generator.py
        T.RUNS.pop(rid, None)                       # fresh target state for this run
        rng, t, prompts, window = random.Random(rid * 7919), 0.0, 0, (0.0, 0)
        while True:
            t += rng.expovariate(freq / 60.0)       # Poisson arrivals
            if t >= DURATION_S: break
            if cap is not None:                     # fixed-window rate limit, as in mock_gateway.py
                ws, c = window
                if t - ws >= 60.0: ws, c = t, 0
                if c >= cap: window = (ws, c); continue   # suppressed: never reaches the target
                window = (ws, c + 1)
            prompts += 1
            if T.decide(rid, t, em, fm)["decision"] == "approve_error":
                wins.append(prompts); break
    return len(wins) / n, (round(sum(wins) / len(wins), 1) if wins else "")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", metavar="LAB_RESULTS_CSV")
    a = ap.parse_args()
    if a.check:
        lab = {(r["condition"], int(r["prompt_freq_per_min"])): r for r in csv.DictReader(open(a.check))}
        bad = 0
        for c in CONDS:
            for f in FREQS:
                sr, mp = run_cell(c, f); row = lab[(c, f)]
                if abs(sr - float(row["attack_success_rate"])) > 1e-9 or str(mp) != row["mean_prompts_to_compromise"]:
                    bad += 1; print("MISMATCH", c, f, sr, mp, dict(row))
        print(f"{35 - bad} of 35 lab rows reproduced exactly")
    else:
        with open("sensitivity_results.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["error_multiplier", "condition", "prompt_freq_per_min",
                        "attack_success_rate", "mean_prompts_to_compromise"])
            for m in MULTIPLIERS:
                for c in ["number_matching", "combined"]:
                    for f in FREQS:
                        sr, mp = run_cell(c, f, err_mult=m)
                        w.writerow([m, c, f, round(sr, 3), mp])
        print("Done -> sensitivity_results.csv")
