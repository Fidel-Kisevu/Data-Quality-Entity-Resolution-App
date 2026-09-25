import json, collections
from pathlib import Path

# Load injected baseline
issues = json.load(open("../data/ground_truth/injected_issues.json"))
injected = collections.Counter(i["rule_id"] for i in issues)

# Detected counts from /quality/run
detected = {
    "COMP-01": 6, "COMP-02": 4, "COMP-03": 2, "COMP-04": 14, "COMP-05": 4, "COMP-06": 7,
    "VAL-01": 4, "VAL-03": 14, "VAL-04": 4, "VAL-05": 5, "VAL-06": 7,
    "UNIQ-02": 488, "CONS-01": 20, "CONS-02": 38, "CONS-03": 51, "CONS-04": 205,
    "ANOM-01": 8, "ANOM-02": 14,
}

print(f'{"Rule":<10} {"Injected":>10} {"Detected":>10} {"Recall":>10}')
print("-" * 45)

all_rules = sorted(set(injected) | set(detected))
for rule in all_rules:
    inj = injected.get(rule, 0)
    det = detected.get(rule, 0)
    if inj > 0:
        recall_str = f"{det / inj * 100:.0f}%"
    else:
        recall_str = "n/a"

    marker = ""
    if inj and det < inj * 0.9:
        marker = "  <-- under"
    elif inj and det > inj * 1.5:
        marker = "  <-- over"

    print(f"{rule:<10} {inj:>10} {det:>10} {recall_str:>10}{marker}")

# Rules missing from detection entirely
print()
print("--- Rules injected but NOT detected at all ---")
for rule in sorted(injected):
    if rule not in detected:
        print(f"  {rule}: injected={injected[rule]}, detected=0")

# Rules detected but never injected
print()
print("--- Rules detected but NOT in ground truth ---")
for rule in sorted(detected):
    if rule not in injected:
        print(f"  {rule}: detected={detected[rule]}")