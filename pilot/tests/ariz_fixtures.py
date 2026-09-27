"""Complete ARIZ records for the wafer-cleaning regression scenario."""
from copy import deepcopy


OUTPUTS = {
    "1.1": "Remove wafer particles without changing the fine-pattern geometry.",
    "1.2": "The cleaning flow acts on particles and exposed wafer patterns.",
    "1.3": "Higher flow removes particles but increases pattern stress; lower flow preserves patterns but leaves particles.",
    "1.4": "Choose particle removal versus pattern stress because removal is the useful function.",
    "1.5": "At the limiting high flow, removal improves while fragile patterns may collapse.",
    "1.6": "Keep particle removal while preventing stress transfer to the fine patterns.",
    "1.7": "Even arbitrarily strong bulk flow must not impose damaging force on the patterns.",
    "2.1": "The operating zone is the particle-pattern-fluid contact region.",
    "2.2": "T1 is fluid arrival, T2 is detachment, and T3 is removal of the detached particle.",
    "2.3": "Existing resources include the cleaning fluid, flow timing, particle surface, and chamber space.",
    "2.4": "Use existing timing and fluid resources before introducing a new substance.",
    "3.1": "The particle leaves the wafer while the pattern remains intact without extra equipment.",
    "3.2": "Use the existing fluid and process timing rather than assume an additional protective material.",
    "3.3": "The cleaning force must be high for detachment and low for pattern preservation.",
    "3.4": "Fluid momentum transfer must be strong at the particle and weak at the pattern.",
    "3.5": "The existing flow transfers momentum selectively at the particle interface.",
    "4.1": "Model fluid agents pushing the particle while avoiding load transfer to pattern walls.",
    "4.2": "Allow a short detachment pulse, then lower the flow during particle transport.",
    "7.1": "A pulse followed by gentle transport partly approaches IFR; selective detachment remains unverified.",
    "7.2": "Temporal separation is a hypothesis, not proof that the detachment pulse avoids the stress tradeoff.",
    "7.3": "Check pulse overshoot, particle redeposition, and throughput loss using pressure, residue, and cycle-time measurements.",
    "7.4": "Pattern preservation is mandatory; microscopy after the pulse must establish compliance before adoption.",
}


def ariz_payload(part):
    data = {"steps": [{"step_code": code, "status": "DONE", "output": output}
                      for code, output in OUTPUTS.items() if code.startswith(f"{part}.")]}
    if part == 4:
        data["solution_directions"] = ["Use a short detachment pulse followed by gentle particle transport."]
    if part == 7:
        data["verdicts"] = [{"idea_title": "Original solution", "ifr_satisfaction_pct": 50,
            "is_tradeoff": False, "side_effects": ["Pulse overshoot", "Redeposition", "Throughput loss"],
            "constraint_ok": False, "note": "Pattern preservation still requires microscopy."}]
    return deepcopy(data)
