# TCM AI Health Advisor API

> AI-powered TCM health advisor based on the Funnel Syndrome Differentiation model — Backend API service for developers and secondary development

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)

---

> **This project provides backend API service only.** Web UI and TUI are pending modules that require secondary developers to implement.

---

## Features

- **Five-Round Structured Inquiry** — Progressive consultation protocol from chief complaint to lifestyle background
- **TCM Syndrome Differentiation** — Eight Principles, Zang-Fu, Specialized Differentiation with spatiotemporal context (season / time / region)
- **Western Medicine Reference** — Red flag detection, possible conditions, recommended tests
- **Formula Recommendation** — Classic formulas → Time-specific formulas → Modern formulas, filtered by safety rules
- **RESTful API** — Full Swagger documentation at `/docs`
- **Safety Mechanisms** — Hardcoded red flag interception, toxic herb shielding, Eighteen Antagonisms & Nineteen Incompatibilities rules
- **🖥️ Web App** — ⏳ Pending (Suggested: Vue 3 / React / any frontend framework)
- **🖥️ TUI Terminal** — ⏳ Pending (Suggested: Textual / Rich / any TUI framework)
- **🌍 Multilingual** — ⏳ Pending (Backend ready, frontend i18n toggle needed)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Interface                   │
│    ┌──────────────┐    ┌──────────────────┐    │
│    │ Web (Pending) │    │ TUI (Pending)     │    │
│    └──────┬───────┘    └────────┬─────────┘    │
├───────────┼─────────────────────┼──────────────┤
│           │      API Layer      │              │
│           └──────► FastAPI ◄────┘              │
├────────────────────────────────────────────────┤
│                  Core Engines                    │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Inquiry     │ │ TCM       │ │ Western      │  │
│  │ Engine      │ │ Diagnosis │ │ Reference    │  │
│  │ (5 rounds)  │ │ (Funnel)  │ │ (Red flags)  │  │
│  └────────────┘ └──────────┘ └──────────────┘  │
│  ┌────────────┐                                 │
│  │ Safety      │ ← Conflicts / Toxicity Shield  │
│  │ Rules       │                                 │
│  └────────────┘                                 │
├────────────────────────────────────────────────┤
│               LLM Interface                     │
│     DeepSeek (primary)  |  Claude (auxiliary)   │
└─────────────────────────────────────────────────┘
```

### Funnel Syndrome Differentiation Model

```
Eight Principles (Yin-Yang · Exterior-Interior · Cold-Hot · Deficiency-Excess)
       ↓
Zang-Fu Differentiation (locate affected organs)
       ↓
Specialized Differentiation (Six Meridians / Wei-Qi-Ying-Blood / Constitution / Qi-Blood-Fluids)
       ↓
Spatiotemporal Weighting (season · time · region)
       ↓
Formula Matching → Safety Filter → Output Recommendation
```

---

## Requirements

| Environment | Version |
|-------------|---------|
| Python | 3.11+ |
| OS | Windows / macOS / Linux |
| API Key | [DeepSeek](https://platform.deepseek.com/) (required) |
| API Key | [Anthropic Claude](https://console.anthropic.com/) (optional) |

> Only one API key (DeepSeek or Claude) is required. Enable "Single Model Mode" via the settings API if you only have one key — the system will automatically route all tasks to your available provider.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ydsgangge-ux/Master-yizhe.git
cd Master-yizhe/backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key — edit data/config.json
# Or use the /api/settings endpoint after startup

# Start the API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Visit http://localhost:8000/docs for Swagger API documentation
```

### Configure API Key

Edit `backend/data/config.json`:

```json
{
  "deepseek": {
    "api_key": "sk-your-deepseek-key",
    "api_url": "https://api.deepseek.com",
    "model": "deepseek-chat"
  },
  "claude": {
    "api_key": "",
    "api_url": "https://api.anthropic.com/v1/messages",
    "model": "claude-sonnet-4-20250514"
  }
}
```

> Only fill in one of the API keys. The system will use whichever key is available.

---

## Project Structure

```
tcm-ai/
├── backend/
│   ├── core/
│   │   ├── inquiry_engine.py      # Five-round inquiry engine
│   │   ├── tcm_engine.py          # TCM diagnosis engine (funnel model)
│   │   ├── western_engine.py      # Western medicine reference engine
│   │   ├── safety_guard.py        # Safety rules engine
│   │   ├── gender_differentiation.py  # Gender-specific differentiation
│   │   └── config.py              # Configuration management
│   ├── routers/
│   │   ├── inquiry.py             # Inquiry API
│   │   ├── analysis.py            # Analysis API
│   │   ├── health.py              # Health records API
│   │   └── settings.py            # Settings API
│   ├── data/
│   │   ├── danger_signals.json    # Red flag checklist
│   │   ├── herb_conflicts.json    # 18/Antagonisms & 19/Incompatibilities
│   │   ├── season_weights.json    # Seasonal weight config
│   │   └── shichen_map.json       # Time-meridian mapping
│   ├── prompts/                   # LLM prompt templates
│   ├── models/                    # Data models
│   ├── main.py                    # FastAPI entry point
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Docker build file
├── frontend/                      # ⏳ Pending — Web frontend
│   ├── src/
│   │   ├── views/                 # ⏳ Pages (Inquiry / Results / History / Settings)
│   │   ├── components/            # ⏳ Components (Chat bubble / Cards, etc.)
│   │   ├── api/                   # ⏳ API client
│   │   ├── locales/               # ⏳ i18n locale files
│   │   └── assets/                # ⏳ Styles & assets
│   ├── package.json               # ⏳
│   └── vite.config.js             # ⏳
├── backend/tui/                   # ⏳ Pending — TUI terminal interface
│   ├── app.py                     # ⏳ TUI entry point
│   ├── screens/                   # ⏳ Feature screens
│   └── widgets/                   # ⏳ Custom widgets
├── .gitignore
├── LICENSE
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/session/start` | Create inquiry session |
| POST | `/api/inquiry/message` | Send message (SSE streaming) |
| POST | `/api/inquiry/analyze` | Start analysis |
| GET | `/api/settings` | Get configuration |
| POST | `/api/settings/deepseek` | Save DeepSeek config |

Full interactive documentation is available at `/docs` (Swagger UI) after starting the server.

---

## Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| Red Flag Detection | Chest pain, sudden severe headache, hematemesis, etc. — hardcoded interception, bypasses LLM |
| Toxic Herb Shielding | Aconite, arisaema, and other toxic herbs excluded from recommendations |
| Herb Conflicts | Local hardcoded rules for Eighteen Antagonisms & Nineteen Incompatibilities, enforced before output |
| Confidence Levels | 🟢 High → provide plan / 🟡 Medium → continue inquiry / 🔴 Low → advise doctor visit |

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| Backend | Python 3.11+ / FastAPI / Uvicorn |
| Web Frontend | ⏳ Pending (Suggested: Vue 3 / React + Vite) |
| TUI Framework | ⏳ Pending (Suggested: Textual) |
| Primary LLM | DeepSeek API (inquiry + TCM diagnosis) |
| Auxiliary LLM | Anthropic Claude API (western reference + tongue analysis) |
| HTTP Client | httpx (async) |
| Storage | SQLite |
| Safety | Local JSON rules engine |
| i18n | ⏳ Pending (Suggested: vue-i18n) |

---

## Secondary Development Guide

This project is an API-only backend. To build a complete application, you need to:

### Web Frontend (Pending)

Suggested pages and features:

| Page | Function | API Endpoint |
|------|----------|-------------|
| Inquiry | Chat-style dialogue with SSE streaming | `POST /api/inquiry/message` |
| Analysis Result | Syndrome differentiation, formula recommendations, confidence display | `POST /api/inquiry/analyze` |
| History | Past consultation records list and details | `GET /api/health/records` |
| Settings | API Key configuration, model selection | `GET/POST /api/settings` |

Suggested stack: Vue 3 + Vite + Vue Router + vue-i18n, or React / any frontend framework.

### TUI Terminal Interface (Pending)

Suggested features:

| Feature | Description |
|---------|-------------|
| Welcome Screen | Session creation, language selection |
| Inquiry Screen | Chat-style dialogue, hotkey to trigger analysis |
| Result Screen | Syndrome differentiation display, formula recommendations |
| Settings Screen | API Key configuration |

Suggested stack: Python Textual framework.

### Development Notes

1. **Implement SSE handling** — The inquiry endpoint uses Server-Sent Events for streaming responses
2. **Handle safety alerts** — Parse and display red flag warnings from the API
3. **Multilingual support** — Backend supports Chinese and English; frontend needs i18n toggle logic
4. **Add your own disclaimer** — You MUST include a medical disclaimer in your frontend (see below)

Refer to the Swagger documentation at `/docs` for complete API specifications.

---

## Disclaimer

**IMPORTANT — PLEASE READ CAREFULLY**

1. **This project is for technical research and educational purposes only.** It does NOT constitute any form of medical diagnosis, treatment advice, or professional medical opinion.

2. **This system is NOT a medical device.** It has NOT been certified or approved by any medical regulatory authority (including but not limited to the NMPA, FDA, or CE).

3. **All analysis results are for reference only.** They MUST NOT be used as the sole basis for any medical decision. Always consult a licensed healthcare professional for diagnosis and treatment.

4. **The formula recommendations generated by this system MUST NOT be used directly for self-medication.** Incorrect use of herbal formulas may result in serious health consequences.

5. **The developers and contributors of this project shall NOT be held liable** for any direct or indirect damages, including but not limited to health deterioration, adverse reactions, economic losses, or any other consequences arising from the use of or reliance on this system.

6. **Users who integrate this API into their own applications are solely responsible** for ensuring compliance with all applicable laws and regulations in their jurisdiction, including but not limited to medical device regulations, data privacy laws, and consumer protection laws.

7. **By using this software, you acknowledge and agree** that you have read, understood, and accept all the terms of this disclaimer. If you do not agree, you must NOT use this software.

---

## License

MIT License — see [LICENSE](LICENSE) file.

---

<p align="center">
  <sub>For technical research only · Not a medical device · Not a substitute for professional medical advice</sub>
</p>
