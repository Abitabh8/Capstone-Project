# Capstone 2 Lab - Human-Centric Authentication Attack Simulation
Everything runs on 127.0.0.1 inside your Kali VM. No real identity provider, push
notification, credential, user or external network is involved.

Components (Figure 4.1): event_generator.py -> mock_gateway.py -> simulated_target.py
Extra: reset_walkthrough.py (mock recovery service, one test account)

Run:  ./run_lab.sh 200
Outputs: lab_results.csv, gateway_log.csv, reset_results.txt
Requirements: Python 3 only (preinstalled on Kali). No pip installs.
