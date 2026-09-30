"""SK hynix DART agent entry point.

Pipeline:
1) Collect structured OpenDART financial statements and raw JSON.
2) Build standalone Q1/Q2/Q3/Q4 from cumulative filings.
3) Leave 2010-2014 unfilled unless a verified legacy CSV is supplied.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
env = os.environ.copy()
env.setdefault("START_YEAR", "2010")

subprocess.run([sys.executable, str(ROOT / "update_data.py")], check=True, env=env)
subprocess.run([sys.executable, str(ROOT / "normalize_quarters.py")], check=True, env=env)
print("SK hynix DART agent completed.")
