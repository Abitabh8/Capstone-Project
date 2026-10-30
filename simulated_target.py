#!/usr/bin/env python3
"""
simulated_target.py  --  Component 3 of 3 (Figure 4.1)
Mock user-facing approval interface. A probabilistic agent, NOT a real person.
Models the compliance budget (Beautement et al. [3]): each prompt drains attention,
quiet time restores it, and error probability rises with fatigue.
Listens on 127.0.0.1 only. Stdlib only.
"""
import json, random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

P_ERR_MIN, P_ERR_MAX, GAMMA = 0.002, 0.45, 1.7
FATIGUE_PER_PROMPT, RECOVERY_PER_MIN = 0.10, 0.35
RUNS = {}   # run_id -> dict(fatigue, last_t, rng)

def decide(run_id, sim_t, err_mult, fatigue_mult):
    st = RUNS.setdefault(run_id, dict(fatigue=0.0, last_t=None, rng=random.Random(run_id)))
    if st["last_t"] is not None:
        st["fatigue"] = max(0.0, st["fatigue"] - RECOVERY_PER_MIN * (sim_t - st["last_t"]) / 60.0)
    pressure = st["fatigue"]
    p = min(1.0, (P_ERR_MIN + (P_ERR_MAX - P_ERR_MIN) * pressure ** GAMMA) * err_mult)
    approved = st["rng"].random() < p
    st["fatigue"] = min(1.0, st["fatigue"] + FATIGUE_PER_PROMPT * fatigue_mult)
    st["last_t"] = sim_t
    return dict(decision="approve_error" if approved else "deny", pressure=round(pressure, 4))

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        out = decide(body["run_id"], body["sim_t"], body["err_mult"], body["fatigue_mult"])
        data = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

if __name__ == "__main__":
    print("Simulated target listening on 127.0.0.1:9002 (loopback only)")
    ThreadingHTTPServer(("127.0.0.1", 9002), H).serve_forever()
