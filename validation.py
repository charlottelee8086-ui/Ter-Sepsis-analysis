from __future__ import annotations

from typing import Any


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    for ch in ["-", "_", "/", "(", ")", "[", "]", "{", "}", ",", ";", ":"]:
        text = text.replace(ch, " ")
    return " ".join(text.split())


def normalize_bio(value: Any) -> str:
    value = str(value or "").lower().strip()
    value = value.replace("-", "")
    value = value.replace("_", "")
    value = value.replace(" ", "")
    value = value.replace("(", "")
    value = value.replace(")", "")
    value = value.replace("/", "")
    return value


def token_overlap_score(a: str, b: str) -> float:
    ta = set(normalize_text(a).split())
    tb = set(normalize_text(b).split())

    if not ta or not tb:
        return 0.0

    overlap = len(ta & tb)
    return overlap / max(1, len(ta))


def score_claim_match(statement: dict, claim: dict) -> float:
    score = 0.0

    stmt_bio = {normalize_bio(x) for x in statement.get("biomarkers", []) if x}
    claim_bio = {normalize_bio(x) for x in claim.get("matched_biomarkers", []) if x}

    bio_overlap = len(stmt_bio & claim_bio)
    if bio_overlap > 0:
        score += 0.5

    intent = statement.get("intent", "other")
    task_type = str(claim.get("task_type", "other")).lower()

    if intent == "diagnosis" and "diagnosis" in task_type:
        score += 0.2
    elif intent == "prognosis" and "prognosis" in task_type:
        score += 0.2
    elif intent == "treatment" and ("therapy" in task_type or "treatment" in task_type):
        score += 0.2
    elif intent in task_type:
        score += 0.2

    score += 0.3 * token_overlap_score(statement.get("text", ""), claim.get("text", ""))

    return round(score, 3)


def _row_auc_value(row: dict) -> Any:
    for key in ["AUC", "auc", "Max_AUC", "max_auc"]:
        val = row.get(key, "")
        if val != "":
            return val
    return ""


def _row_population_value(row: dict) -> Any:
    for key in ["population", "Population", "pops", "Pop"]:
        val = row.get(key, "")
        if val != "":
            return val
    return ""


def validate_statement(
    statement: dict, claims: list[dict], clinical_rows: list[dict]
) -> dict:
    matched_claims = []

    for claim in claims:
        s = score_claim_match(statement, claim)
        if s >= 0.45:
            matched_claims.append({**claim, "match_score": s})

    matched_claims.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    supporting_claims = [c for c in matched_claims if c.get("polarity") == "support"]
    attacking_claims = [c for c in matched_claims if c.get("polarity") == "attack"]

    stmt_norm = {normalize_bio(x) for x in statement.get("biomarkers", []) if x}

    relevant_rows = []
    seen_rows = set()

    for row in clinical_rows:

        def expand_alias(x):
            x = normalize_bio(x)
            aliases = {x}

            if x in ["crp", "c-reactiveprotein"]:
                aliases |= {"crp", "creactiveprotein"}

            if x in ["pct", "procalcitonin"]:
                aliases |= {"pct", "procalcitonin"}

            if x in ["wbc", "whitebloodcell"]:
                aliases |= {"wbc", "whitebloodcell"}

            if x in ["lactate", "serumlactate"]:
                aliases |= {"lactate", "serumlactate"}

            return aliases

        stmt_norm = set()
        for b in statement.get("biomarkers", []):
            stmt_norm |= expand_alias(b)

        row_names = set()
        for k in ["brief", "name", "Biomarker_name", "Brief_name"]:
            row_names |= expand_alias(row.get(k, ""))

        if stmt_norm & row_names:
            relevant_rows.append(row)

        if stmt_norm and (stmt_norm & row_names):
            key = tuple(sorted(n for n in row_names if n))
            if key in seen_rows:
                continue
            seen_rows.add(key)
            relevant_rows.append(row)

    support_score = round(sum(c["match_score"] for c in supporting_claims), 3)
    conflict_score = round(sum(c["match_score"] for c in attacking_claims), 3)

    if support_score > 0 and conflict_score == 0:
        verdict = "supported"
    elif support_score > 0 and conflict_score > 0:
        verdict = "conflicted"
    elif support_score == 0 and conflict_score > 0:
        verdict = "challenged"
    else:
        verdict = "insufficient_evidence"

    relevant_rows.sort(
        key=lambda r: (
            (
                0 if _row_auc_value(r) == "" else -float(_row_auc_value(r)),
                str(r.get("name", "")),
            )
            if str(_row_auc_value(r)).replace(".", "", 1).isdigit()
            else (1, str(r.get("name", "")))
        )
    )

    return {
        "statement": statement.get("text", ""),
        "intent": statement.get("intent", "other"),
        "biomarkers": statement.get("biomarkers", []),
        "supporting_claims": supporting_claims[:5],
        "attacking_claims": attacking_claims[:5],
        "support_score": support_score,
        "conflict_score": conflict_score,
        "verdict": verdict,
        "clinical_rows": relevant_rows[:5],
    }


def summarize_validation(results: list[dict]) -> dict:
    counts = {
        "supported": 0,
        "conflicted": 0,
        "challenged": 0,
        "insufficient_evidence": 0,
    }

    for r in results:
        verdict = r.get("verdict", "insufficient_evidence")
        counts[verdict] = counts.get(verdict, 0) + 1

    if counts["challenged"] > 0:
        overall = "partially_supported"
    elif counts["conflicted"] > 0:
        overall = "mixed_evidence"
    elif counts["supported"] > 0 and counts["insufficient_evidence"] == 0:
        overall = "well_supported"
    else:
        overall = "limited_support"

    return {
        "overall_verdict": overall,
        "counts": counts,
    }
