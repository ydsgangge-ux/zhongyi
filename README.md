# 🌿 Master-yizhe（问诊）

> 基于漏斗辨证模型的 AI 中医健康顾问系统

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)

---

## ✨ 功能特性

- **🏥 五轮结构化问诊** — 从主诉到生活背景的渐进式问诊协议
- **🧠 中医辨证分析** — 八纲、脏腑、专项辨证 + 时空背景感知（季节/时辰/地域）
- **⚕️ 西医参考** — 危险信号识别、可能疾病方向、检查建议
- **💊 方剂推荐** — 经方优先 → 时方 → 现代方，经安全规则库过滤
- **🖥️ 双界面** — Web 网页端 + TUI 终端界面
- **🌍 多语言** — 中文 / English 一键切换，基于 vue-i18n
- **🛡️ 安全机制** — 危险信号硬编码拦截、毒性药材屏蔽、十八反十九畏规则

> ⚠️ **免责声明**：本系统为健康参考工具，不构成执业诊断。所有建议请结合专业医师意见。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────┐
│                  用户界面层                       │
│    ┌──────────────┐    ┌──────────────────┐     │
│    │   Web (Vue3)  │    │   TUI (Textual)   │     │
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

## 📋 环境要求

| 环境 | 要求 |
|------|------|
| Python | 3.11+ |
| Node.js | 18+ |
| 操作系统 | Windows / macOS / Linux |
| API Key | [DeepSeek](https://platform.deepseek.com/)（必填） |
| API Key | [Anthropic Claude](https://console.anthropic.com/)（可选） |

---

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 克隆仓库
git clone https://github.com/your-username/tcm-ai.git
cd tcm-ai

# Windows：双击 start.bat
# 或命令行：
python launcher.py
```

启动后浏览器自动打开 `http://localhost:5328`。

### 手动启动

```bash
# 1. 后端环境
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. 前端环境
cd ../frontend
npm install

# 3. 启动后端（自动提供前端页面）
cd ../backend
python -m uvicorn main:app --host 0.0.0.0 --port 5328

# 浏览器访问 http://localhost:5328
```

### 启动 TUI 界面

```bash
cd backend
python run_tui.py
```

### 配置 API Key

首次启动后访问设置页 `http://localhost:5328/settings`，或在文件中编辑：

**Web 设置页** — 推荐，图形界面操作

**手动编辑配置文件** — `backend/data/config.json`

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

> 💡 只需填写 DeepSeek API Key 即可使用全部核心功能。Claude 为可选增强项（用于舌象分析和西医参考）。

---

## 📁 项目结构

```
tcm-ai/
├── backend/
│   ├── core/
│   │   ├── inquiry_engine.py      # 五轮问诊引擎
│   │   ├── tcm_engine.py          # 中医辨证引擎（漏斗模型）
│   │   ├── western_engine.py      # 西医参考引擎
│   │   ├── safety_guard.py        # 安全规则库
│   │   └── config.py              # 配置管理
│   ├── routers/
│   │   ├── inquiry.py             # 问诊 API
│   │   ├── analysis.py            # 分析 API
│   │   ├── health.py              # 健康记录 API
│   │   └── settings.py            # 设置 API
│   ├── tui/                       # 终端界面 (Textual)
│   │   ├── app.py                 # TUI 应用入口
│   │   ├── screens/               # 各功能屏幕
│   │   └── widgets/               # 自定义组件
│   ├── data/
│   │   ├── danger_signals.json    # 危险信号清单
│   │   ├── herb_conflicts.json    # 十八反/十九畏规则
│   │   ├── season_weights.json    # 季节权重配置
│   │   └── shichen_map.json       # 时辰经络映射
│   ├── prompts/                   # LLM 提示词模板
│   ├── models/                    # 数据模型
│   ├── main.py                    # FastAPI 入口
│   ├── requirements.txt           # Python 依赖
│   └── run_tui.py                 # TUI 启动脚本
├── frontend/
│   ├── src/
│   │   ├── views/                 # 页面（问诊/结果/历史/设置）
│   │   ├── components/            # 组件（气泡/卡片等）
│   │   ├── api/                   # API 调用封装
│   │   └── assets/                # 样式资源
│   ├── package.json
│   └── vite.config.js
├── launcher.py                     # 一键启动脚本
├── start.bat                      # Windows 快捷启动
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚙️ 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Python 3.11+ / FastAPI / Uvicorn |
| 前端框架 | Vue 3 / Vite / Vue Router |
| TUI 框架 | Textual |
| 主力 LLM | DeepSeek API（问诊 + 中医辨证） |
| 辅助 LLM | Anthropic Claude API（西医参考 + 舌象分析） |
| HTTP 客户端 | httpx (async) / axios |
| 数据存储 | SQLite |
| 安全规则 | 本地 JSON 规则引擎 |

---

## 🛡️ 安全机制

| 机制 | 说明 |
|------|------|
| 🚨 危险信号拦截 | 胸痛、突发剧烈头痛、呕血等硬编码检测，不走 LLM 判断 |
| 🚫 毒性药材屏蔽 | 附子、川乌等毒性药材不出现在推荐处方 |
| 📋 十八反/十九畏 | 本地硬编码规则库，AI 输出前强制过滤 |
| 🎯 置信度分级 | 🟢 高置信→给方案 / 🟡 中置信→继续追问 / 🔴 低置信→建议就医 |

---

## 🔧 开发说明

### API 文档

启动服务后访问 `http://localhost:5328/docs` 查看 Swagger UI 自动生成的 API 文档。

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/session/start` | 创建问诊会话 |
| POST | `/api/inquiry/message` | 发送消息（SSE 流式响应） |
| POST | `/api/inquiry/analyze` | 开始分析 |
| GET | `/api/settings` | 获取配置 |
| POST | `/api/settings/deepseek` | 保存 DeepSeek 配置 |

---

## 🌍 多语言 / i18n

Web 端支持中文和 English 一键切换：

- 点击导航栏右侧的 **「EN/中文」** 按钮即可切换语言
- 语言选择自动保存到浏览器 localStorage，刷新不丢失
- 基于 [vue-i18n](https://vue-i18n.intlify.org/) 实现

**添加新语言：**

1. 在 `frontend/src/locales/` 下新建语言文件（如 `ja.js`）
2. 在 `frontend/src/locales/index.js` 中注册
3. 在 `App.vue` 的切换按钮中添加选项

**翻译覆盖范围：**

| 模块 | 翻译项 |
|------|--------|
| 导航栏 | 标题、菜单、页脚 |
| 问诊页面 | 表单标签、按钮、提示语 |
| 聊天组件 | 角色名称（中医顾问/Me） |
| 分析报告 | 所有字段标签、置信度等级 |
| 设置页面 | 表单标签、状态提示、保存反馈 |
| 历史记录 | 标题、空状态提示 |

> ⚠️ 注意：LLM 返回的问诊对话内容为实时生成，不受界面语言影响。分析报告中的医学术语保持原文。

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE) 文件。

---

<p align="center">
  <sub>健康参考用途 · For health reference only · 非执业诊断 · Not a substitute for professional medical advice</sub>
</p>
