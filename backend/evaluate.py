"""
Local evaluation smoke tests. These are transparent deterministic checks,
not a substitute for Guild's hosted evaluation runtime.
Run: python evaluate.py
"""
import json
from tools import emergency_check, estimate_cost, provider_search_links

cases = [
    {
        "name": "gas leak safety escalation",
        "description": "There is a gas smell near the stove.",
        "expected_emergency": True
    },
    {
        "name": "routine washer issue",
        "description": "The washer will not spin and makes a clicking sound.",
        "expected_emergency": False
    },
    {
        "name": "electrical sparking escalation",
        "description": "The outlet is sparking when I plug in the vacuum.",
        "expected_emergency": True
    }
]

results = []
for case in cases:
    actual = bool(emergency_check(case["description"]))
    passed = actual == case["expected_emergency"]
    results.append({"test": case["name"], "passed": passed, "actual_emergency": actual})

assert estimate_cost("plumbing")["verified"] is False
assert "google.com/maps" in provider_search_links("plumbing", "San Francisco")[0]["url"]

report = {
    "suite": "fixit-ai-smoke-tests",
    "passed": sum(1 for r in results if r["passed"]),
    "total": len(results),
    "results": results
}
print(json.dumps(report, indent=2))
with open("evaluation-report.json", "w") as f:
    json.dump(report, f, indent=2)
if report["passed"] != report["total"]:
    raise SystemExit(1)
