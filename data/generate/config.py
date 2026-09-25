"""
DataQ — Dataset Generation Config
Seeded for full reproducibility.
"""

SEED = 42

# Canonical entity counts
N_CANONICAL_CUSTOMERS = 200
N_ERP_TRANSACTIONS = 450

# Source overlap & duplication rates
CRM_COVERAGE = 0.92          # % of canonical that appear in CRM
ERP_COVERAGE = 0.78
MKT_COVERAGE = 0.85

WITHIN_SOURCE_DUP_RATE = 0.03   # exact dups inside one source
CROSS_SOURCE_MATCH_RATE = 0.70  # of shared entities that should match

# Injection rates (approximate)
COMPLETENESS_RATE = 0.06
VALIDITY_RATE = 0.04
CONFLICT_RATE = 0.07
ANOMALY_RATE = 0.015

# Output paths (relative to project root)
SAMPLES_DIR = "data/samples"
GROUND_TRUTH_DIR = "data/ground_truth"
