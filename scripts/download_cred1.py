"""Download CRED-1 domain credibility dataset from GitHub.

Run once:  python scripts/download_cred1.py

Saves to data/cred1_current.json for use by source_reliability.
Dataset: https://github.com/aloth/cred-1 (CC BY 4.0)
"""

import json
import os
import urllib.request

URL = "https://raw.githubusercontent.com/aloth/cred-1/main/data/cred1_current.json"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUT_PATH = os.path.join(DATA_DIR, "cred1_current.json")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Downloading CRED-1 from {URL}...")
    with urllib.request.urlopen(URL, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=0)
    print(f"Saved {len(data)} domains to {OUT_PATH}")


if __name__ == "__main__":
    main()
