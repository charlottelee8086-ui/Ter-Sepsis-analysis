<<<<<<< HEAD
# Ter-Sepsis-analysis
Our objectives are identify the symptoms of sepsis, propose appropriate treatment strategies, and evaluate their effectiveness as well as potential long-term side effects.
=======
# 🧠 Sepsis Diagnostic Platform  
### Multi-language AI + Biomarker Database + Clinical Reasoning

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 🚀 Overview

A full-stack clinical decision support system for **sepsis diagnosis**, integrating:

- 🧬 Biomarker Database (AUC, cutoff, clinical evidence)
- 🌳 Argument–Clinical reasoning framework
- 🤖 AI-powered diagnosis (Google Gemini)
- 🌍 Multi-language interface (English / 中文 / Français)

Users can:
- Explore biomarker evidence
- Understand clinical reasoning paths
- Input real-world clinical cases
- Receive AI-generated diagnostic analysis
- Switch seamlessly between three languages

---

# 🧠 Sepsis Diagnostic Platform  
### Multi-language AI + Biomarker Database + Clinical Reasoning

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 🚀 Overview

A full-stack clinical decision support system for **sepsis diagnosis**, integrating:

- 🧬 Biomarker Database (AUC, cutoff, clinical evidence)
- 🌳 Argument–Clinical reasoning framework
- 🤖 AI-powered diagnosis (Google Gemini)
- 🌍 Multi-language interface (English / 中文 / Français)

Users can:
- Explore biomarker evidence
- Understand clinical reasoning paths
- Input real-world clinical cases
- Receive AI-generated diagnostic analysis
- Switch seamlessly between three languages

---

## 🌐 Features

### 🌍 Multi-language Interface
- 🇬🇧 English / 🇨🇳 中文 / 🇫🇷 Français
- Full UI + AI output language switching

### 🧬 Biomarker Database
- Filter by:
  - Population (Adult / Children / Neonatal)
  - Application (Diagnosis / Prognosis)
  - Category (Inflammation, Immune, Organ Dysfunction…)
  - Drug targets
- Includes:
  - AUC values
  - Cut-off thresholds
  - Sensitivity / Specificity
  - Clinical summaries

### 🌳 Argument–Clinical Mapping
- Evidence-driven reasoning structure  
- Links:

- Transparent clinical reasoning

### 🤖 AI Diagnosis (Gemini)
- Input: EN / 中文 / FR
- Pipeline:
1. Biomarker extraction
2. Database retrieval
3. Risk estimation
4. Treatment recommendations
- Output language follows UI
- Streaming response

---

## 🖥️ Interface Preview

> Replace with screenshots


### Home
![Home Screenshot](docs/home.png)

### Biomarker Database
![Database Screenshot](docs/db.png)

### Clinical Report
![Report Screenshot](docs/report.png)

### AI Diagnosis
![AI Screenshot](docs/ai.png)

---

## Project Structure

sepsis_project/
│
├── app.py # FastAPI backend (Gemini integration)
├── sepsis_project.html # Frontend (multi-language UI)
├── requirements.txt # Python dependencies
├── .env # API key (NOT committed)
├── .venv/ # Virtual environment
└── README.md


---

---

## Installation

> 📌 Follow these steps to run the project locally.

### 1. Clone repository

```bash
git clone <your-repo-url>
cd sepsis_project

python -m venv .venv

source .venv/Scripts/activate

.venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

GOOGLE_API_KEY=your_api_key_here

python -m uvicorn app:app --host 127.0.0.1 --port 8000

http://127.0.0.1:8000（Open in browser）
>>>>>>> c444e2e (Initial commit)
