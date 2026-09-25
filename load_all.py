"""
Upload + ingest all sample files with correct source_systems.
Run from repo root with the backend venv's python.
"""
from pathlib import Path
import httpx

BASE = "http://localhost:8000"

FILES = [
    ("data/samples/crm_customers.csv", "CRM"),
    ("data/samples/erp_customers.csv", "ERP"),
    ("data/samples/erp_transactions.csv", "ERP"),
    ("data/samples/marketing_customers.xlsx", "MKT"),
]

with httpx.Client(timeout=120.0) as client:
    for filepath, source_system in FILES:
        p = Path(filepath)
        if not p.exists():
            print(f"SKIP {filepath} — not found")
            continue

        print(f"\n=== {filepath} -> {source_system} ===")

        try:
            with p.open("rb") as f:
                r = client.post(
                    f"{BASE}/sources/upload",
                    params={"source_system": source_system},
                    files={"file": (p.name, f, "application/octet-stream")},
                )
            if r.status_code != 200:
                print(f"  UPLOAD FAILED: {r.status_code} -- {r.text[:300]}")
                continue
            source = r.json()
            source_id = source["id"]
            print(f"  Uploaded: id={source_id}  source_system={source['source_system']}")

            r = client.post(f"{BASE}/sources/{source_id}/ingest")
            if r.status_code != 200:
                print(f"  INGEST FAILED: {r.status_code} -- {r.text[:300]}")
                continue
            result = r.json()
            print(f"  Ingested: entity_type={result['entity_type']}  rows_inserted={result['rows_inserted']}")

        except Exception as e:
            print(f"  ERROR: {e}")

print("\n=== Done ===")