import json
import os
from pathlib import Path
from typing import List, Optional, AsyncIterator

import requests
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "sepsis_project.html"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
BIOMARKER_API = os.getenv("BIOMARKER_API_URL", "http://sysbio.org.cn/SBD/api.php")


class ExtractedCase(BaseModel):
    markers: List[str]
    population: Optional[str] = "adult"
    severity: Optional[str] = None
    suspected_source: Optional[str] = None


class DiagnoseRequest(BaseModel):
    clinical_case: str
    language: str = "en"


app = FastAPI(title="Sepsis Gemini Backend")


LANG_LABELS = {
    "en": {
        "phase_extract_active": "Extracting biomarkers...",
        "phase_extract_done": "markers extracted",
        "phase_db_active": "Querying database...",
        "phase_db_done": "matched",
        "phase_report_active": "Streaming report...",
        "phase_report_done": "Complete",
        "case_prefix": "Clinical case",
        "db_empty": "No database records found for the extracted markers.",
        "ctx_population": "Population",
        "ctx_severity": "Severity",
        "ctx_source": "Suspected source",
        "ctx_markers": "Key markers",
    },
    "zh": {
        "phase_extract_active": "正在提取生物标志物…",
        "phase_extract_done": "个指标已提取",
        "phase_db_active": "正在查询数据库…",
        "phase_db_done": "个匹配",
        "phase_report_active": "正在生成报告…",
        "phase_report_done": "完成",
        "case_prefix": "临床病例",
        "db_empty": "未找到与提取标志物对应的数据库记录。",
        "ctx_population": "人群",
        "ctx_severity": "严重程度",
        "ctx_source": "疑似感染来源",
        "ctx_markers": "关键标志物",
    },
    "fr": {
        "phase_extract_active": "Extraction des biomarqueurs…",
        "phase_extract_done": "marqueurs extraits",
        "phase_db_active": "Interrogation de la base de données…",
        "phase_db_done": "correspondances",
        "phase_report_active": "Génération du rapport en cours…",
        "phase_report_done": "Terminé",
        "case_prefix": "Cas clinique",
        "db_empty": "Aucune donnée de base n’a été trouvée pour les biomarqueurs extraits.",
        "ctx_population": "Population",
        "ctx_severity": "Sévérité",
        "ctx_source": "Source suspectée",
        "ctx_markers": "Biomarqueurs clés",
    },
}


def normalize_language(language: Optional[str]) -> str:
    language = (language or "en").lower().strip()
    if language not in {"en", "zh", "fr"}:
        return "en"
    return language


def get_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, detail="GOOGLE_API_KEY is not set on the server."
        )
    return genai.Client(api_key=api_key)


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def extraction_instruction(language: str = "en") -> str:
    language = normalize_language(language)
    if language == "zh":
        return (
            "你是一名脓毒症分诊临床数据提取助手。"
            "请阅读病例，并且只返回结构化 JSON。"
            "提取与脓毒症相关的实验室生物标志物和临床指标。"
            "在别名明显时进行标准化，例如 leukocyte count -> WBC，serum lactate -> lactate，IL-6 -> IL6。"
            "仅保留最相关的 1 到 8 个指标，并按重要性排序。"
            "根据年龄推断 population：adult、children、neonatal。"
            "如可能，根据病例推断 severity：SIRS、sepsis、severe、shock、syndrome。"
            "如病例明确，推断 suspected_source，例如 UTI、pneumonia、abdominal、line infection、neonatal EOS。"
            "不要输出解释。"
        )
    if language == "fr":
        return (
            "Vous êtes un assistant d’extraction de données cliniques pour le triage du sepsis. "
            "Lisez le cas et retournez uniquement un JSON structuré. "
            "Extrayez les biomarqueurs biologiques et les indicateurs cliniques pertinents pour le sepsis. "
            "Normalisez les alias quand c’est évident, par exemple leukocyte count -> WBC, serum lactate -> lactate, IL-6 -> IL6. "
            "Gardez seulement les 1 à 8 marqueurs les plus pertinents par ordre de priorité. "
            "Déduisez la population à partir de l’âge : adult, children, neonatal. "
            "Déduisez la sévérité si possible : SIRS, sepsis, severe, shock, syndrome. "
            "Déduisez suspected_source si elle est claire, par exemple UTI, pneumonia, abdominal, line infection, neonatal EOS. "
            "N’ajoutez aucune explication."
        )
    return (
        "You are a clinical data-extraction assistant for sepsis triage. "
        "Read the case and return only structured JSON. "
        "Extract laboratory biomarkers and clinical indicators relevant to sepsis. "
        "Normalize aliases when obvious, for example leukocyte count -> WBC, serum lactate -> lactate, IL-6 -> IL6. "
        "Keep only the most relevant 1 to 8 markers in priority order. "
        "Infer population from age: adult, children, neonatal. "
        "Infer severity if possible from the case: SIRS, sepsis, severe, shock, syndrome. "
        "Infer suspected_source if clearly present, such as UTI, pneumonia, abdominal, line infection, neonatal EOS. "
        "Do not include explanations."
    )


def diagnosis_system_prompt(language: str = "en") -> str:
    language = normalize_language(language)
    base = (
        "You are an expert clinical AI assistant specialized in sepsis risk assessment. "
        "You are helping with research and decision support, not issuing definitive medical orders. "
        "Use the case details first, then integrate biomarker database evidence if present. "
        "Do not invent cutoffs, AUC values, or guideline details. If evidence is missing, say so explicitly. "
        "When possible, estimate qSOFA or discuss SOFA-relevant organ dysfunction using only the data given. "
        "Keep the output practical, concise, and clinician-friendly. "
    )

    if language == "zh":
        return (
            base
            + "请用简体中文输出完整报告。"
            + "严格使用以下粗体章节标题："
            + "**生物标志物分析**、**脓毒症评估**、**概率**、**治疗建议**、**风险分层**。"
            + "在治疗建议中，优先讨论即时稳定、感染源控制、培养、抗生素、液体复苏、升压药、监测和 ICU 升级。"
            + "在概率部分，明确写出一个百分比并给出简短理由。"
        )
    if language == "fr":
        return (
            base
            + "Veuillez rédiger l’intégralité du rapport en français. "
            + "Utilisez exactement les sections en gras suivantes : "
            + "**Analyse des biomarqueurs**, **Évaluation du sepsis**, **Probabilité**, **Recommandations thérapeutiques**, **Stratification du risque**. "
            + "Dans les recommandations thérapeutiques, priorisez la stabilisation immédiate, le contrôle de la source, les prélèvements, les antibiotiques, les fluides, les vasopresseurs, la surveillance et l’escalade vers les soins intensifs si justifié. "
            + "Dans la section Probabilité, indiquez un pourcentage explicite et une justification brève."
        )
    return (
        base
        + "Format your response with these EXACT sections using **bold** headings: "
        + "**Biomarker Analysis**, **Sepsis Assessment**, **Probability**, **Treatment Recommendations**, **Risk Stratification**. "
        + "Under Treatment Recommendations, prioritize immediate stabilization, source control, cultures, antibiotics, fluids, vasopressors, monitoring, and ICU escalation when supported by the case. "
        + "For Probability, state one explicit percentage and a brief rationale."
    )


def extract_case(client: genai.Client, clinical_case: str, language: str = "en") -> ExtractedCase:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[extraction_instruction(language), f"Clinical case:\n\n{clinical_case}"],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedCase,
            temperature=0,
        ),
    )
    text = response.text or "{}"
    data = json.loads(text)
    extracted = ExtractedCase(**data)
    if not extracted.markers:
        extracted.markers = ["PCT", "CRP", "WBC"]
    return extracted


def fetch_biomarker_data(name: str, population: Optional[str]) -> list:
    params = {"name": name}
    if population:
        params["population"] = population
    try:
        res = requests.get(BIOMARKER_API, params=params, timeout=8)
        if not res.ok:
            return []
        payload = res.json()
        results = payload if isinstance(payload, list) else payload.get("results", [])
        return results[:3] if isinstance(results, list) else []
    except Exception:
        return []


def build_reference_data(markers: List[str], population: Optional[str]):
    found_markers = []
    reference_chunks = []
    for marker in markers[:6]:
        rows = fetch_biomarker_data(marker, population)
        if rows:
            found_markers.append(marker)
            reference_chunks.append(
                f'--- {marker} Evidence ({population or "unknown"}) ---'
            )
            reference_chunks.append(json.dumps(rows, indent=2, ensure_ascii=False))
    return found_markers, "\n".join(reference_chunks)


@app.get("/")
def index():
    return FileResponse(HTML_FILE)


@app.get("/api/health")
def health():
    return JSONResponse(
        {
            "ok": True,
            "model": MODEL_NAME,
            "google_api_key_configured": bool(os.getenv("GOOGLE_API_KEY")),
        }
    )


@app.post("/api/diagnose")
async def diagnose(req: DiagnoseRequest):
    if not req.clinical_case.strip():
        raise HTTPException(status_code=400, detail="clinical_case is required")

    client = get_client()
    language = normalize_language(req.language)
    labels = LANG_LABELS[language]

    async def event_stream() -> AsyncIterator[str]:
        try:
            yield sse(
                {
                    "type": "phase",
                    "index": 0,
                    "state": "active",
                    "message": labels["phase_extract_active"],
                }
            )
            extracted = extract_case(client, req.clinical_case, language)
            yield sse(
                {
                    "type": "phase",
                    "index": 0,
                    "state": "done",
                    "message": f"{len(extracted.markers)} {labels['phase_extract_done']}",
                }
            )

            yield sse(
                {
                    "type": "phase",
                    "index": 1,
                    "state": "active",
                    "message": labels["phase_db_active"],
                }
            )
            found_markers, reference_data = build_reference_data(
                extracted.markers, extracted.population
            )
            yield sse(
                {
                    "type": "markers",
                    "extracted_markers": extracted.markers,
                    "found_markers": found_markers,
                    "population": extracted.population,
                    "severity": extracted.severity,
                    "suspected_source": extracted.suspected_source,
                    "language": language,
                }
            )
            yield sse(
                {
                    "type": "phase",
                    "index": 1,
                    "state": "done",
                    "message": f"{len(found_markers)}/{min(len(extracted.markers), 6)} {labels['phase_db_done']}",
                }
            )

            yield sse(
                {
                    "type": "phase",
                    "index": 2,
                    "state": "active",
                    "message": labels["phase_report_active"],
                }
            )
            user_prompt = (
                f"{labels['case_prefix']}:\n{req.clinical_case}\n\n"
                f"Extracted Context:\n"
                f"- {labels['ctx_population']}: {extracted.population or 'unknown'}\n"
                f"- {labels['ctx_severity']}: {extracted.severity or 'unspecified'}\n"
                f"- {labels['ctx_source']}: {extracted.suspected_source or 'unspecified'}\n"
                f"- {labels['ctx_markers']}: {', '.join(extracted.markers)}\n\n"
                f"Biomarker Reference Data:\n{reference_data or labels['db_empty']}\n\n"
                "Generate the final assessment now."
            )

            full_report = []
            stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=diagnosis_system_prompt(language),
                    temperature=0.2,
                ),
            )
            for chunk in stream:
                text = chunk.text or ""
                if text:
                    full_report.append(text)
                    yield sse({"type": "report_chunk", "text": text})

            final_report = "".join(full_report).strip()
            yield sse(
                {
                    "type": "phase",
                    "index": 2,
                    "state": "done",
                    "message": labels["phase_report_done"],
                }
            )
            yield sse({"type": "done", "report": final_report, "language": language})
        except HTTPException as e:
            yield sse({"type": "error", "message": e.detail})
        except Exception as e:
            yield sse({"type": "error", "message": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
