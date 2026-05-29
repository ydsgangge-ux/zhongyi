# 🌿 Master-yizhe (AI Health Consultant)

> AI-powered TCM health advisor built on the Funnel Syndrome Differentiation model

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)

---

## ✨ Features

- **🏥 Five-Round Structured Inquiry** — Progressive consultation protocol from chief complaint to lifestyle background
- **🧠 TCM Syndrome Differentiation** — Eight Principles, Zang-Fu, Specialized Differentiation with spatiotemporal context (season / time / region)
- **⚕️ Western Medicine Reference** — Red flag detection, possible conditions, recommended tests
- **💊 Formula Recommendation** — Classic formulas → Time-specific formulas → Modern formulas, filtered by safety rules
- **🖥️ Dual Interface** — Web app + TUI terminal interface
- **🌍 Multilingual** — Chinese / English one-click toggle via vue-i18n
- **🛡️ Safety Mechanisms** — Hardcoded red flag interception, toxic herb shielding, Eighteen/Antagonisms & Nineteen/Incompatibilities rules

> ⚠️ **Disclaimer**: This system is a health reference tool and does not constitute a professional medical diagnosis. Please consult a licensed practitioner for all health decisions.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Interface                   │
│    ┌──────────────┐    ┌──────────────────┐    │
│    │  Web (Vue 3)  │    │  TUI (Textual)   │    │
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
└────────────────────────────────────────────────┘
```

### Funnel Syndrome Differentiation Model

```
Eight Principles (Yin-Yang · Exterior-Interior · Cold-Heat · Deficiency-Excess)
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

## 📋 Requirements

| Environment | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| OS | Windows / macOS / Linux |
| API Key | [DeepSeek](https://platform.deepseek.com/) (required) |
| API Key | [Anthropic Claude](https://console.anthropic.com/) (optional) |

> 💡 Only one API key (DeepSeek or Claude) is required. Enable "Single Model Mode" on the Settings page if you only have one key — the system will automatically route all tasks to your available provider.

---

## 🚀 Quick Start

### One-Click Launch

```bash
git clone https://github.com/ydsgangge-ux/Master-yizhe.git
cd Master-yizhe

# Windows: double-click start.bat
# Linux/macOS: ./start.sh
# or command line:
python launcher.py
```

The browser will open `http://localhost:5328` automatically.

### Manual Setup

```bash
# 1. Backend
cd backend
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
pip install -r requirements.txt

# 2. Frontend
cd ../frontend
npm install

# 3. Start backend (serves frontend as well)
cd ../backend
python -m uvicorn main:app --host 0.0.0.0 --port 5328

# Open http://localhost:5328 in your browser
```

### Launch TUI

```bash
# Windows: double-click start_tui.bat
# Linux/macOS: ./start_tui.sh
# or directly:
cd backend
python run_tui.py
```

### Configure API Key

On first launch, visit the Settings page at `http://localhost:5328/settings`, or edit the config file manually:

**Web Settings** — Recommended, GUI-based configuration

**Manual config** — `backend/data/config.json`

```json
{
  "deepseek": {
    "api_key": "sk-your-deepseek-key",
    "api_url": "https://api.deepseek.com",
    "model": "deepseek-chat"
  },
  "claude": {
    "api_key": "sk-ant-your-claude-key",
    "api_url": "https://api.anthropic.com/v1/messages",
    "model": "claude-sonnet-4-20250514"
  }
}
```

> 💡 Only fill in one of the API keys. The system will use whichever key is available.

---

## 📁 Project Structure

```
tcm-ai/
├── backend/
│   ├── core/
│   │   ├── inquiry_engine.py      # Five-round inquiry engine
│   │   ├── tcm_engine.py          # TCM diagnosis engine (funnel model)
│   │   ├── western_engine.py      # Western medicine reference engine
│   │   ├── safety_guard.py        # Safety rules engine
│   │   └── config.py              # Configuration management
│   ├── routers/
│   │   ├── inquiry.py             # Inquiry API
│   │   ├── analysis.py            # Analysis API
│   │   ├── health.py              # Health records API
│   │   └── settings.py            # Settings API
│   ├── tui/                       # Terminal UI (Textual)
│   │   ├── app.py                 # TUI entry point
│   │   ├── screens/               # Feature screens
│   │   └── widgets/               # Custom widgets
│   ├── data/
│   │   ├── danger_signals.json    # Red flag checklist
│   │   ├── herb_conflicts.json    # 18/Antagonisms & 19/Incompatibilities
│   │   ├── season_weights.json    # Seasonal weight config
│   │   └── shichen_map.json       # Time-meridian mapping
│   ├── prompts/                   # LLM prompt templates
│   ├── models/                    # Data models
│   ├── main.py                    # FastAPI entry point
│   ├── requirements.txt           # Python dependencies
│   └── run_tui.py                 # TUI launcher
├── frontend/
│   ├── src/
│   │   ├── views/                 # Pages (Inquiry / Results / History / Settings)
│   │   ├── components/            # Components (Chat bubble / Cards, etc.)
│   │   ├── api/                   # API client
│   │   └── assets/                # Styles & assets
│   ├── package.json
│   └── vite.config.js
├── launcher.py                    # One-click launcher
├── start.bat                      # Windows quick start
├── start.sh                       # Linux/macOS quick start
├── start_tui.bat                  # Windows TUI quick start
├── start_tui.sh                   # Linux/macOS TUI quick start
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚙️ Tech Stack

| Category | Technology |
|----------|-----------|
| Backend | Python 3.11+ / FastAPI / Uvicorn |
| Frontend | Vue 3 / Vite / Vue Router |
| TUI | Textual |
| Primary LLM | DeepSeek API (inquiry + TCM diagnosis) |
| Auxiliary LLM | Anthropic Claude API (western reference + tongue analysis) |
| HTTP Client | httpx (async) / axios |
| Storage | SQLite |
| Safety | Local JSON rules engine |

---

## 🛡️ Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| 🚨 Red Flag Detection | Chest pain, sudden severe headache, hematemesis, etc. — hardcoded interception, bypasses LLM |
| 🚫 Toxic Herb Shielding | Aconite, arisaema, and other toxic herbs excluded from recommendations |
| 📋 Herb Conflicts | Local hardcoded rules for Eighteen Antagonisms & Nineteen Incompatibilities, enforced before output |
| 🎯 Confidence Levels | 🟢 High → provide plan / 🟡 Medium → continue inquiry / 🔴 Low → advise doctor visit |

---

## 🔧 Development

### API Documentation

After starting the service, visit `http://localhost:5328/docs` for the auto-generated Swagger UI.

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/session/start` | Create inquiry session |
| POST | `/api/inquiry/message` | Send message (SSE streaming) |
| POST | `/api/inquiry/analyze` | Start analysis |
| GET | `/api/settings` | Get configuration |
| POST | `/api/settings/deepseek` | Save DeepSeek config |

---

## 🌍 Internationalization (i18n)

The web interface supports Chinese and English with one-click toggle:

- Click the **"EN/中文"** button on the right side of the navigation bar
- Language preference is saved to browser localStorage and persisted across refreshes
- Powered by [vue-i18n](https://vue-i18n.intlify.org/)

**Adding a new language:**

1. Create a new locale file under `frontend/src/locales/` (e.g. `ja.js`)
2. Register it in `frontend/src/locales/index.js`
3. Add a toggle option in `App.vue`

**Translation coverage:**

| Module | Items Translated |
|--------|-----------------|
| Navigation | Title, menu, footer |
| Inquiry Page | Form labels, buttons, prompts |
| Chat Component | Role names (TCM Advisor / Me) |
| Analysis Report | All field labels, confidence levels |
| Settings Page | Form labels, status hints, save feedback |
| History | Title, empty state prompt |

> ⚠️ Note: LLM-generated consultation dialogue content is real-time and not affected by the interface language. Medical terminology in analysis reports is preserved as-is.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

<p align="center">
  <sub>For health reference only · Not a substitute for professional medical advice</sub>
</p>