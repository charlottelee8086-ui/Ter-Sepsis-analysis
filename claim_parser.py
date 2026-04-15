import re
from biomarker_matcher import find_biomarkers


SECTION_TITLES = {
    "biomarker analysis",
    "sepsis assessment",
    "probability",
    "treatment recommendations",
    "risk stratification",
    "生物标志物分析",
    "脓毒症评估",
    "概率",
    "治疗建议",
    "风险分层",
    "analyse des biomarqueurs",
    "évaluation du sepsis",
    "probabilité",
    "recommandations thérapeutiques",
    "stratification du risque",
}


def split_into_sentences(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    lines = [x.strip() for x in text.splitlines() if x.strip()]
    chunks = []

    for line in lines:
        # Remove markdown headings / bullets / numbering
        line = re.sub(r"^\#+\s*", "", line)
        line = re.sub(r"^\*+\s*", "", line)
        line = re.sub(r"^[-•]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        line = line.strip()

        if not line:
            continue

        # Skip pure bold section headers like **Biomarker Analysis**
        line_plain = re.sub(r"\*+", "", line).strip().lower()
        if line_plain in SECTION_TITLES:
            continue

        parts = re.split(r"[;]+", line)
        for p in parts:
            p = p.strip()
            if len(p) >= 12:
                chunks.append(p)

    return chunks


def infer_intent(sentence: str) -> str:
    s = sentence.lower()

    if any(k in s for k in [
        "diagnos", "sepsis", "infection", "screen", "identify",
        "shock", "qsofa", "sofa", "organ dysfunction"
    ]):
        return "diagnosis"

    if any(k in s for k in [
        "mortality", "prognosis", "outcome", "survival", "readmission"
    ]):
        return "prognosis"

    if any(k in s for k in [
        "hydrocortisone", "steroid", "antibiotic", "vasopressor",
        "treatment", "therapy", "fluid", "resuscitation"
    ]):
        return "treatment"

    return "other"


def extract_statements_from_report(report_text: str, alias_map: dict) -> list[dict]:
    statements = []

    for sent in split_into_sentences(report_text):
        sent_clean = re.sub(r"\*+", "", sent).strip()
        if not sent_clean:
            continue

        biomarkers = find_biomarkers(sent_clean, alias_map)
        statements.append({
            "text": sent_clean,
            "intent": infer_intent(sent_clean),
            "biomarkers": biomarkers,
        })

    return statements
