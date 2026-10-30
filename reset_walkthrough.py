#!/usr/bin/env python3
"""
reset_walkthrough.py  --  Safe password-reset walkthrough (Phase 3)
Runs entirely in-process against a MOCK account-recovery service holding ONE
dedicated test account. No network, no real service, no real credentials.

It compares recovery designs against one scenario: a requester who knows only
PUBLIC details about the account owner. Each control maps to OWASP's Forgot
Password Cheat Sheet and to the "weak recovery verification" weakness [6][17].
Usage: python3 reset_walkthrough.py
"""
import time, secrets

class MockRecovery:
    def __init__(self, design):
        self.d = design
        self.account = dict(user="test.user", email="test.user@lab.invalid",
                            dob="2000-01-01", pet="rex",       # "public" facts
                            token=None, token_t=0, used=False, alerts=[], attempts=0)
    def request_reset(self, user):
        if self.d["consistent_response"] or user == self.account["user"]:
            msg = "If the account exists, a reset message was sent."  # no enumeration
        else:
            msg = "No such account."
        return msg
    def verify_identity(self, answers, owner_confirmed_in_app=False):
        a = self.account; a["attempts"] += 1
        if self.d["rate_limit"] and a["attempts"] > 3: return "BLOCKED: rate limit"
        if self.d["knowledge_based"]:                          # weak: public-info answers
            if answers.get("dob") == a["dob"] and answers.get("pet") == a["pet"]:
                return "OK"
            return "FAIL"
        if self.d["owner_confirmation"] and not owner_confirmed_in_app:
            a["alerts"].append("Reset requested - was this you?")
            return "BLOCKED: waiting for owner confirmation (alert sent)"
        return "OK"
    def complete_reset(self, new_pw, waited_s=0):
        a = self.account
        if self.d["cooling_off_s"] and waited_s < self.d["cooling_off_s"]:
            return "BLOCKED: cooling-off period"
        if self.d["notify"]: a["alerts"].append("Your password was changed.")
        return "RESET COMPLETE"

DESIGNS = {
    "A. Weak (knowledge-based questions only)":
        dict(knowledge_based=True,  consistent_response=False, rate_limit=False, owner_confirmation=False, cooling_off_s=0,  notify=False),
    "B. Partial (rate limit + notification)":
        dict(knowledge_based=True,  consistent_response=True,  rate_limit=True,  owner_confirmation=False, cooling_off_s=0,  notify=True),
    "C. Hardened (OWASP-aligned: owner confirmation, cooling-off, alerts)":
        dict(knowledge_based=False, consistent_response=True,  rate_limit=True,  owner_confirmation=True,  cooling_off_s=86400, notify=True),
}

def scenario(name, d):
    svc = MockRecovery(d)
    print(f"\n=== {name} ===")
    print(" request_reset ->", svc.request_reset("test.user"))
    enum = svc.request_reset("nobody")
    print(" enumeration probe ->", enum, "(LEAKS account existence)" if "No such" in enum else "(consistent)")
    # requester knows only public details (name/DOB/pet from social media)
    res = "FAIL"
    for guess in [dict(dob="2000-01-01", pet="rex")]:
        res = svc.verify_identity(guess, owner_confirmed_in_app=False)
    print(" identity check with PUBLIC info only ->", res)
    outcome = "ACCOUNT TAKEN OVER" if res == "OK" and "COMPLETE" in svc.complete_reset("x", waited_s=0) else "ATTACK STOPPED"
    print(" outcome ->", outcome, "| alerts to owner:", svc.account["alerts"] or "none")
    return outcome

if __name__ == "__main__":
    print("Safe password-reset walkthrough (mock service, test account only)")
    results = {n: scenario(n, d) for n, d in DESIGNS.items()}
    print("\n=== Summary ===")
    for n, r in results.items(): print(f" {r:20s} {n}")
