#!/usr/bin/env python3
"""
mock_gateway.py  --  Component 2 of 3 (Figure 4.1)
Stands in for a real identity provider. Receives login-attempt events from the
generator, applies the selected mitigation, forwards surviving prompts to the
simulated target, and records approve/deny. No real push, credential or IdP.
Listens on 127.0.0.1 only. Writes gateway_log.csv. Stdlib only.
"""
import csv, json, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MITIGATIONS = {
    "none":            dict(err_mult=1.00, fatigue_mult=1.00, rate_cap=None, clarity=0.0),
    "rate_limiting":   dict(err_mult=1.00, fatigue_mult=1.00, rate_cap=3,    clarity=0.0),
    "context_rich":    dict(err_mult=0.55, fatigue_mult=0.85, rate_cap=None, clarity=0.7),
    "number_matching": dict(err_mult=0.02, fatigue_mult=1.00, rate_cap=None, clarity=0.5),
    "combined":        dict(err_mult=0.02, fatigue_mult=0.85, rate_cap=3,    clarity=1.0),
}
STATE = dict(cond="none", windows={})   # windows: run_id -> (window_start, count)
LOG = open("gateway_log.csv", "w", newline="", buffering=1)   # line-buffered: nothing lost when the runner stops the gateway
W = csv.writer(LOG)
W.writerow(["run_id", "condition", "sim_t", "outcome", "decision_pressure"])

def post(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, obj):
        d = json.dumps(obj).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/config":
            STATE["cond"] = b["condition"]; STATE["windows"].clear(); LOG.flush()
            return self._send({"ok": True})
        m = MITIGATIONS[STATE["cond"]]; rid, t = b["run_id"], b["sim_t"]
        if m["rate_cap"] is not None:                       # rate limiting
            ws, n = STATE["windows"].get(rid, (0.0, 0))
            if t - ws >= 60.0: ws, n = t, 0
            if n >= m["rate_cap"]:
                STATE["windows"][rid] = (ws, n)
                W.writerow([rid, STATE["cond"], round(t, 2), "suppressed", ""])
                return self._send({"outcome": "suppressed"})
            STATE["windows"][rid] = (ws, n + 1)
        r = post("http://127.0.0.1:9002/", dict(run_id=rid, sim_t=t,
                 err_mult=m["err_mult"], fatigue_mult=m["fatigue_mult"]))
        W.writerow([rid, STATE["cond"], round(t, 2), r["decision"], r["pressure"]])
        self._send({"outcome": r["decision"]})

if __name__ == "__main__":
    print("Mock MFA gateway listening on 127.0.0.1:9001 (loopback only)")
    ThreadingHTTPServer(("127.0.0.1", 9001), H).serve_forever()
