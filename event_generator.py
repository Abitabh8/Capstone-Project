#!/usr/bin/env python3
"""
event_generator.py  --  Component 1 of 3 (Figure 4.1)
Emits SIMULATED authentication-prompt events (Poisson arrivals) to the local mock
gateway. Sends no real logins, notifications or credentials. Uses simulated
timestamps, so a 15-minute attack runs in seconds. Writes lab_results.csv.
Usage: python3 event_generator.py [--runs 200]
"""
import argparse, csv, json, random, urllib.request

CONDS = ["none", "rate_limiting", "context_rich", "number_matching", "combined"]
FREQS = [1, 2, 5, 10, 15, 20, 30]
DURATION_MIN = 15.0

def post(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def one_run(run_id, freq):
    rng, t, prompts = random.Random(run_id * 7919), 0.0, 0
    while True:
        t += rng.expovariate(freq / 60.0)
        if t >= DURATION_MIN * 60: return False, prompts, None
        r = post("http://127.0.0.1:9001/event", dict(run_id=run_id, sim_t=t))
        if r["outcome"] != "suppressed": prompts += 1
        if r["outcome"] == "approve_error": return True, prompts, t

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", type=int, default=200)
    n = ap.parse_args().runs; rid = 0
    with open("lab_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition", "prompt_freq_per_min", "attack_success_rate", "mean_prompts_to_compromise"])
        for cond in CONDS:
            post("http://127.0.0.1:9001/config", {"condition": cond})
            for freq in FREQS:
                wins, pc = 0, []
                for _ in range(n):
                    rid += 1
                    ok, p, _t = one_run(rid, freq)
                    if ok: wins += 1; pc.append(p)
                row = [cond, freq, round(wins / n, 3), round(sum(pc) / len(pc), 1) if pc else ""]
                w.writerow(row); print(row, flush=True)
    print("Done -> lab_results.csv and gateway_log.csv")
