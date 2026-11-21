import json
import os
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "deepseek": {
        "api_key": "",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 500,
    },
    "claude": {
        "api_key": "",
        "api_url": "https://api.anthropic.com/v1/messages",
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
    },
    "system": {
        "region_default": "",
        "save_history": True,
        "single_model_mode": False,
    },
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return _deep_merge(DEFAULT_CONFIG.copy(), saved)
        except (json.JSONDecodeError, IOError):
            pass

    config = DEFAULT_CONFIG.copy()

    env_deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    env_claude_key = os.getenv("CLAUDE_API_KEY", "")
    if env_deepseek_key:
        config["deepseek"]["api_key"] = env_deepseek_key
    if env_claude_key:
        config["claude"]["api_key"] = env_claude_key

    return config


def save_config(config: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_deepseek_config() -> dict:
    return load_config().get("deepseek", DEFAULT_CONFIG["deepseek"])


def get_claude_config() -> dict:
    config = load_config()
    if config.get("system", {}).get("single_model_mode", False):
        ds = config.get("deepseek", {})
        if ds.get("api_key") and not config.get("claude", {}).get("api_key"):
            return {
                "api_key": ds["api_key"],
                "api_url": ds["api_url"],
                "model": ds["model"],
                "max_tokens": 1500,
            }
    return config.get("claude", DEFAULT_CONFIG["claude"])


def get_system_config() -> dict:
    return load_config().get("system", DEFAULT_CONFIG["system"])


def _is_masked_key(value) -> bool:
    return isinstance(value, str) and "****" in value


def update_deepseek_config(**kwargs) -> dict:
    config = load_config()
    for k, v in kwargs.items():
        if v is None:
            continue
        # 前端回填的是脱敏 Key（sk-xxxx****），不能覆盖真实 Key
        if k == "api_key" and _is_masked_key(v):
            continue
        config["deepseek"][k] = v
    save_config(config)
    return config["deepseek"]


def update_claude_config(**kwargs) -> dict:
    config = load_config()
    for k, v in kwargs.items():
        if v is None:
            continue
        if k == "api_key" and _is_masked_key(v):
            continue
        config["claude"][k] = v
    save_config(config)
    return config["claude"]


def update_system_config(**kwargs) -> dict:
    config = load_config()
    for k, v in kwargs.items():
        if v is not None:
            config["system"][k] = v
    save_config(config)
    return config["system"]


def is_configured() -> dict:
    config = load_config()
    ds_ok = bool(config["deepseek"]["api_key"])
    claude_ok = bool(config["claude"]["api_key"])
    single_mode = config.get("system", {}).get("single_model_mode", False)
    if single_mode and ds_ok:
        claude_ok = True
    if single_mode and claude_ok and not ds_ok:
        ds_ok = True
    return {
        "deepseek": ds_ok,
        "claude": claude_ok,
        "single_model_mode": single_mode,
        "ready": ds_ok or claude_ok,
    }


def get_active_llm(prefer: str = "deepseek") -> dict:
    config = load_config()
    ds = config.get("deepseek", {})
    claude = config.get("claude", {})
    ds_key = ds.get("api_key", "")
    claude_key = claude.get("api_key", "")
    single_mode = config.get("system", {}).get("single_model_mode", False)

    def _ds_cfg():
        return {
            "provider": "deepseek",
            "api_key": ds_key,
            "api_url": ds.get("api_url", ""),
            "model": ds.get("model", "deepseek-chat"),
            "temperature": ds.get("temperature", 0.7),
            "max_tokens": ds.get("max_tokens", 500),
        }

    def _claude_cfg():
        return {
            "provider": "claude",
            "api_key": claude_key,
            "api_url": claude.get("api_url", ""),
            "model": claude.get("model", "claude-sonnet-4-20250514"),
            "temperature": 0.7,
            "max_tokens": claude.get("max_tokens", 1500),
        }

    if prefer == "deepseek":
        if ds_key:
            return _ds_cfg()
        if single_mode and claude_key:
            return _claude_cfg()
    elif prefer == "claude":
        if claude_key and not single_mode:
            return _claude_cfg()
        if ds_key:
            return _ds_cfg()

    if ds_key:
        return _ds_cfg()
    if claude_key:
        return _claude_cfg()

    return {"provider": None, "api_key": "", "api_url": "", "model": "",
            "temperature": 0.7, "max_tokens": 500}


def _deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
