# 中医 AI 健康顾问 API

> 基于漏斗辨证模型的 AI 中医健康顾问系统 — 后端 API 服务，仅供开发者二次开发使用

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)

---

> **本项目仅提供后端 API 服务，不包含任何用户界面。** Web UI 和 TUI 均为待开发模块，需二次开发者自行实现。

---

## 功能特性

- **五轮结构化问诊** — 从主诉到生活背景的渐进式问诊协议
- **中医辨证分析** — 八纲、脏腑、专项辨证 + 时空背景感知（季节/时辰/地域）
- **西医参考** — 危险信号识别、可能疾病方向、检查建议
- **方剂推荐** — 经方优先 → 时方 → 现代方，经安全规则库过滤
- **RESTful API** — 完整 Swagger 文档位于 `/docs`
- **安全机制** — 危险信号硬编码拦截、毒性药材屏蔽、十八反十九畏规则
- **🖥️ Web 网页端** — ⏳ 待开发（建议技术栈：Vue 3 / React / 任意前端框架）
- **🖥️ TUI 终端界面** — ⏳ 待开发（建议技术栈：Textual / Rich / 任意 TUI 框架）
- **🌍 多语言** — ⏳ 待开发（后端已支持，前端需实现 i18n 切换）

---

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                  用户界面层                       │
│    ┌──────────────┐    ┌──────────────────┐     │
│    │  Web (待开发)  │    │  TUI (待开发)     │     │
│    └──────┬───────┘    └────────┬─────────┘     │
├───────────┼─────────────────────┼───────────────┤
│           │      API 层         │               │
│           └──────► FastAPI ◄────┘               │
├─────────────────────────────────────────────────┤
│                   核心引擎                        │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ 问诊引擎    │ │中医辨证引擎│ │西医参考引擎   │   │
│  │ (5轮协议)   │ │(漏斗模型) │ │(危险信号)    │   │
│  └────────────┘ └──────────┘ └──────────────┘   │
│  ┌────────────┐                                  │
│  │ 安全规则库  │ ← 十八反/十九畏/毒性屏蔽        │
│  └────────────┘                                  │
├─────────────────────────────────────────────────┤
│              LLM 接口层                          │
│     DeepSeek (主)  |  Claude (辅)                │
└─────────────────────────────────────────────────┘
```

### 漏斗辨证模型

```
八纲辨证（阴阳·表里·寒热·虚实）
       ↓
脏腑辨证（定位病变脏腑）
       ↓
专项辨证（六经 / 卫气营血 / 体质 / 气血津液）
       ↓
时空权重叠加（季节 · 时辰 · 地域）
       ↓
方剂匹配 → 安全规则过滤 → 输出建议
```

---

## 环境要求

| 环境 | 要求 |
|------|------|
| Python | 3.11+ |
| 操作系统 | Windows / macOS / Linux |
| API Key | [DeepSeek](https://platform.deepseek.com/)（必填） |
| API Key | [Anthropic Claude](https://console.anthropic.com/)（可选） |

> 只需一个 API Key（DeepSeek 或 Claude）即可运行。如只有一个 Key，可通过设置接口启用"单模型模式"，系统会自动将所有任务路由到可用的模型。

---

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/ydsgangge-ux/Master-yizhe.git
cd Master-yizhe/backend

# 创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 API Key — 编辑 data/config.json
# 或启动后通过 /api/settings 接口配置

# 启动 API 服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 访问 http://localhost:8000/docs 查看 Swagger API 文档
```

### 配置 API Key

编辑 `backend/data/config.json`：

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

> 只需填写 DeepSeek API Key 即可使用全部核心功能。Claude 为可选增强项（用于舌象分析和西医参考）。

---

## 项目结构

```
tcm-ai/
├── backend/
│   ├── core/
│   │   ├── inquiry_engine.py      # 五轮问诊引擎
│   │   ├── tcm_engine.py          # 中医辨证引擎（漏斗模型）
│   │   ├── western_engine.py      # 西医参考引擎
│   │   ├── safety_guard.py        # 安全规则库
│   │   ├── gender_differentiation.py  # 性别差异化辨证
│   │   └── config.py              # 配置管理
│   ├── routers/
│   │   ├── inquiry.py             # 问诊 API
│   │   ├── analysis.py            # 分析 API
│   │   ├── health.py              # 健康记录 API
│   │   └── settings.py            # 设置 API
│   ├── data/
│   │   ├── danger_signals.json    # 危险信号清单
│   │   ├── herb_conflicts.json    # 十八反/十九畏规则
│   │   ├── season_weights.json    # 季节权重配置
│   │   └── shichen_map.json       # 时辰经络映射
│   ├── prompts/                   # LLM 提示词模板
│   ├── models/                    # 数据模型
│   ├── main.py                    # FastAPI 入口
│   ├── requirements.txt           # Python 依赖
│   └── Dockerfile                 # Docker 构建文件
├── frontend/                      # ⏳ 待开发 — Web 前端
│   ├── src/
│   │   ├── views/                 # ⏳ 页面（问诊/结果/历史/设置）
│   │   ├── components/            # ⏳ 组件（气泡/卡片等）
│   │   ├── api/                   # ⏳ API 调用封装
│   │   ├── locales/               # ⏳ 多语言文件
│   │   └── assets/                # ⏳ 样式资源
│   ├── package.json               # ⏳
│   └── vite.config.js             # ⏳
├── backend/tui/                   # ⏳ 待开发 — TUI 终端界面
│   ├── app.py                     # ⏳ TUI 应用入口
│   ├── screens/                   # ⏳ 各功能屏幕
│   └── widgets/                   # ⏳ 自定义组件
├── .gitignore
├── LICENSE
└── README.md
```

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/session/start` | 创建问诊会话 |
| POST | `/api/inquiry/message` | 发送消息（SSE 流式响应） |
| POST | `/api/inquiry/analyze` | 开始分析 |
| GET | `/api/settings` | 获取配置 |
| POST | `/api/settings/deepseek` | 保存 DeepSeek 配置 |

启动服务后访问 `/docs` 可查看完整的 Swagger UI 交互式 API 文档。

---

## 安全机制

| 机制 | 说明 |
|------|------|
| 危险信号拦截 | 胸痛、突发剧烈头痛、呕血等硬编码检测，不走 LLM 判断 |
| 毒性药材屏蔽 | 附子、川乌等毒性药材不出现在推荐处方 |
| 十八反/十九畏 | 本地硬编码规则库，AI 输出前强制过滤 |
| 置信度分级 | 🟢 高置信→给方案 / 🟡 中置信→继续追问 / 🔴 低置信→建议就医 |

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Python 3.11+ / FastAPI / Uvicorn |
| Web 前端 | ⏳ 待开发（建议 Vue 3 / React + Vite） |
| TUI 框架 | ⏳ 待开发（建议 Textual） |
| 主力 LLM | DeepSeek API（问诊 + 中医辨证） |
| 辅助 LLM | Anthropic Claude API（西医参考 + 舌象分析） |
| HTTP 客户端 | httpx (async) |
| 数据存储 | SQLite |
| 安全规则 | 本地 JSON 规则引擎 |
| 多语言 | ⏳ 待开发（建议 vue-i18n） |

---

## 二次开发指南

本项目为纯 API 后端，构建完整应用需要你：

### Web 前端（待开发）

建议实现以下页面和功能：

| 页面 | 功能 | 对应 API |
|------|------|---------|
| 问诊页 | 聊天式对话界面，支持 SSE 流式显示 | `POST /api/inquiry/message` |
| 分析结果页 | 辨证结果、方剂推荐、置信度展示 | `POST /api/inquiry/analyze` |
| 历史记录页 | 历史问诊记录列表与详情 | `GET /api/health/records` |
| 设置页 | API Key 配置、模型选择 | `GET/POST /api/settings` |

建议技术栈：Vue 3 + Vite + Vue Router + vue-i18n，或 React / 任意前端框架。

### TUI 终端界面（待开发）

建议实现以下功能：

| 功能 | 说明 |
|------|------|
| 欢迎屏 | 会话创建、语言选择 |
| 问诊屏 | 聊天式对话，快捷键触发分析 |
| 结果屏 | 辨证结果展示、方剂推荐 |
| 设置屏 | API Key 配置 |

建议技术栈：Python Textual 框架。

### 开发要点

1. **实现 SSE 处理** — 问诊接口使用 Server-Sent Events 进行流式响应
2. **处理安全告警** — 解析并展示 API 返回的危险信号警告
3. **多语言支持** — 后端已支持中英文，前端需实现 i18n 切换逻辑
4. **添加免责声明** — 你必须在自己的前端中包含医疗免责声明（见下方）

完整的 API 规范请参考启动后的 `/docs` Swagger 文档。

---

## 免责声明

**重要提示 — 请仔细阅读**

1. **本项目仅供技术研究和教育目的使用。** 不构成任何形式的医疗诊断、治疗建议或专业医疗意见。

2. **本系统不是医疗器械。** 未经过任何医疗器械监管机构（包括但不限于国家药品监督管理局 NMPA、美国 FDA、欧盟 CE）的认证或批准。

3. **所有分析结果仅供参考。** 绝不能作为任何医疗决策的唯一依据。请务必咨询执业医师进行诊断和治疗。

4. **本系统生成的方剂推荐绝不可直接用于自行服药。** 错误使用中药方剂可能导致严重健康后果。

5. **本项目的开发者和贡献者不承担任何责任**，对于因使用或依赖本系统而产生的任何直接或间接损害，包括但不限于健康恶化、不良反应、经济损失或其他后果。

6. **将本 API 集成到自有应用中的用户需自行承担全部责任**，确保遵守所在司法管辖区的所有适用法律法规，包括但不限于医疗器械法规、数据隐私法和消费者保护法。

7. **使用本软件即表示你确认并同意**已阅读、理解并接受本免责声明的所有条款。如不同意，请勿使用本软件。

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。

---

<p align="center">
  <sub>仅供技术研究 · 非医疗器械 · 不能替代专业医疗建议</sub>
</p>
