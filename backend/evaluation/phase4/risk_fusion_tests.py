"""Phase 4 — Part 13: Risk Fusion final evaluation.

Verifies the configured weights, tests the missing-component renormalisation
behaviour across scenarios A–E, and shows one manual calculation.  Weights are
only READ — never modified.
"""

from backend.evaluation.phase4.helpers import service, write_csv, write_json

CONFIGURED = {
    "DCI": 0.25, "NIS": 0.25, "Diabetes": 0.20,
    "Obesity": 0.15, "Hypertension": 0.10, "Deficiency": 0.05,
}


def main() -> dict:
    fusion = service("fusion")
    weights = fusion.config.get("weights", {})
    total = sum(weights.get(k, 0) for k in ["DCI", "NIS", "Diabetes", "Obesity", "Hypertension", "Deficiency"])

    def run(label, dci, nis, dia, ob, hyp, def_):
        score, level = fusion.fuse(dci, nis, dia, ob, hyp, def_)
        return {
            "scenario": label,
            "dci": dci, "nis": nis, "diabetes": dia, "obesity": ob,
            "hypertension": hyp, "deficiency": def_,
            "fused_score": round(score, 6) if score is not None else None,
            "risk_level": level,
        }

    rows = [
        run("A_all_available", 0.8, 0.3, 0.2, 0.3, 0.1, 0.2),
        run("B_dci_unavailable", None, 0.3, 0.2, 0.3, 0.1, 0.2),
        run("C_dci_and_nis_unavailable", None, None, 0.2, 0.3, 0.1, 0.2),
        run("D_subset_only", 0.8, None, 0.2, None, None, None),
        run("E_none_available", None, None, None, None, None, None),
    ]

    # Manual calculation for scenario B.
    avail_w = weights["NIS"] + weights["Diabetes"] + weights["Obesity"] + weights["Hypertension"] + weights["Deficiency"]
    manual = (weights["NIS"] * 0.3 + weights["Diabetes"] * 0.2 + weights["Obesity"] * 0.3
              + weights["Hypertension"] * 0.1 + weights["Deficiency"] * 0.2) / avail_w

    write_csv("risk_fusion_tests.csv", rows)
    summary = {
        "configured_weights": weights,
        "weights_total": round(total, 4),
        "weights_total_is_1": abs(total - 1.0) < 1e-9,
        "renormalisation": "available weights are renormalised to sum to 1; missing components are not fabricated",
        "manual_calculation_scenario_B": {
            "formula": "sum(w_i*v_i for available i) / sum(w_i for available i)",
            "available_weight": round(avail_w, 4),
            "manual_fused_score": round(manual, 6),
            "service_fused_score": rows[1]["fused_score"],
            "match": rows[1]["fused_score"] is not None and abs(rows[1]["fused_score"] - manual) < 1e-6,
        },
        "scenarios": rows,
    }
    write_json("risk_fusion_evaluation.json", summary)
    for r in rows:
        print(f"{r['scenario']:>26}: score={r['fused_score']} level={r['risk_level']}")
    print(f"Configured weights total = {total:.2f}")
    print(f"Manual scenario B fused score = {manual:.6f} (service = {rows[1]['fused_score']})")
    return summary


if __name__ == "__main__":
    main()
