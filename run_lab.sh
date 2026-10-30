#!/usr/bin/env bash
# One-command lab runner. Usage: ./run_lab.sh [runs_per_cell]   (default 200)
set -e
RUNS="${1:-200}"
cd "$(dirname "$0")"
python3 simulated_target.py & T=$!
python3 mock_gateway.py & G=$!
trap 'kill $T $G 2>/dev/null' EXIT
sleep 1.5
python3 event_generator.py --runs "$RUNS"
echo; echo "Password-reset walkthrough:"; python3 reset_walkthrough.py | tee reset_results.txt
echo; echo "Finished. Evidence files: lab_results.csv  gateway_log.csv  reset_results.txt"
