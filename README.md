# Ter-Sepsis Analysis

A sepsis diagnostic decision-support prototype that connects three evidence layers:

1. **LLM-generated clinical diagnosis**
2. **Paper-derived argument claims and evidence**
3. **Clinical biomarker database with AUC / population / application evidence**

The main idea is to use **biomarkers as the bridge** between the LLM diagnosis and literature claims:

```text
Clinical case
  ↓
LLM diagnostic report
  ↓
Clinical statements
  ↓
Biomarker extraction / inference
  ↓
Paper claim matching
  ↓
Support / conflict / insufficient-evidence validation
```

## Features

- Multi-language web interface: English / 中文 / Français
- FastAPI backend
- Google Gemini-based clinical case analysis
- Biomarker extraction from clinical cases
- Paper claim and evidence visualization
- Double validation panel:
  - splits the LLM report into clinical statements
  - links statements to biomarkers
  - matches biomarkers to paper-derived claims
  - labels claims as supporting or conflicting
  - links to clinical biomarker evidence when available

## Project Structure

```text
Ter-Sepsis-analysis/
├── app.py                    # FastAPI backend and Gemini integration
├── sepsis_project.html       # Frontend UI
├── biomarker_matcher.py      # Biomarker aliases and matching logic
├── claim_parser.py           # Splits LLM reports into clinical statements
├── validation.py             # Statement–claim matching and scoring
├── requirements.txt          # Python dependencies
├── Annane_Sepsis_Corpus/
│   └── data.xlsx             # Clinical biomarker database
├── Spesis analysis.ipynb     # Notebook analysis / argument tree work
└── README.md
```

## Matching Logic

The double validation process does not compare the whole LLM report to whole papers directly.

Instead:

1. `claim_parser.py` splits the LLM report into smaller clinical statements.
2. `app.py` infers biomarkers from each statement using:
   - direct alias matching
   - fallback unit-based heuristics, for example:
     - `ng/mL` → PCT
     - `mg/L` → CRP
     - `mmol/L` → Lactate
     - `x10^9/L` or leukocytosis → WBC
3. `validation.py` scores each statement–claim pair using:
   - biomarker overlap
   - task alignment, such as diagnosis / prognosis / treatment
   - text overlap
4. Claims are classified as:
   - `supported`
   - `conflicted`
   - `challenged`
   - `insufficient_evidence`

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/charlottelee8086-ui/Ter-Sepsis-analysis.git
cd Ter-Sepsis-analysis
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Git Bash / macOS / Linux:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Gemini API key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 5. Run the app

```bash
python -m uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

### 6. Check backend health

```text
http://127.0.0.1:8000/api/health
```

You should see:

```json
{
  "ok": true,
  "google_api_key_configured": true
}
```

## Notes

This project is for research and educational use only. It is not a medical device and should not replace clinical judgment, local protocols, or urgent medical evaluation.
