import re

MANUAL_ALIAS = {
    "il6": "IL6",
    "il-6": "IL6",
    "interleukin 6": "IL6",
    "interleukin-6": "IL6",
    "pct": "PCT",
    "procalcitonin": "PCT",
    "crp": "CRP",
    "c reactive protein": "CRP",
    "c-reactive protein": "CRP",
    "lactate": "LACTATE",
    "hla dr": "HLA-DR",
    "hla-dr": "HLA-DR",
    "presepsin": "CD14",
    "supar": "SUPAR",
    "albumin": "ALB",
    "adrenomedullin": "ADM",
}


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("interleukin-6", "il6")
    text = text.replace("interleukin 6", "il6")
    text = text.replace("c-reactive protein", "crp")
    text = text.replace("c reactive protein", "crp")
    text = text.replace("procalcitonin", "pct")
    text = re.sub(r"[^a-z0-9\-\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_alias_map_from_rows(rows: list[dict]) -> dict:
    alias_map = {}
    for row in rows:
        canon = row.get("brief") or row.get("Biomarker_name") or row.get("name")
        if not canon:
            continue

        candidates = [
            row.get("brief", ""),
            row.get("name", ""),
            row.get("Biomarker_name", ""),
            row.get("Brief_name", ""),
        ]

        for c in candidates:
            c = normalize_text(str(c))
            if c and len(c) > 1:
                alias_map[c] = canon

    alias_map.update(MANUAL_ALIAS)
    return alias_map


def find_biomarkers(text: str, alias_map: dict) -> list[str]:
    t = normalize_text(text)
    tokens = set(t.split())
    hits = set()

    for alias, canon in alias_map.items():
        if not alias or len(alias) <= 2:
            continue
        parts = re.findall(r"[a-z0-9]+", alias)
        if not parts:
            continue
        if all(p in tokens for p in parts):
            hits.add(canon)

    return sorted(hits)
