from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button, Input, Checkbox
from textual.binding import Binding
from rich.text import Text
from ...core.config import load_config, save_config, is_configured
from ..i18n import t


class SettingsScreen(Screen):
    CSS = """
    SettingsScreen {
        align: center middle;
    }
    #settings-container {
        width: 70;
        height: auto;
        max-height: 90%;
        padding: 1 3;
        border: round $primary;
        background: $surface;
    }
    #settings-title {
        text-align: center;
        margin-bottom: 1;
    }
    .section-title {
        margin-top: 1;
        margin-bottom: 0;
        color: $primary;
        text-style: bold;
    }
    .section-hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    .form-row {
        height: 3;
        margin-bottom: 0;
    }
    .form-label {
        width: 14;
        padding: 1 1 0 0;
        color: $text-muted;
    }
    .form-input {
        width: 1fr;
    }
    .status-row {
        height: 2;
        margin-bottom: 0;
    }
    .status-label {
        width: 14;
        padding: 0 1 0 0;
    }
    .status-value {
        width: auto;
    }
    #btn-row {
        margin-top: 1;
        height: 3;
    }
    #save-btn {
        margin-right: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "go_back", t("binding.back"), show=True),
        Binding("ctrl+s", "save", t("binding.save"), show=True),
    ]

    def compose(self):
        yield Header()
        with Container(id="settings-container"):
            yield Static(Text(t("settings.title"), style="bold green", justify="center"), id="settings-title")

            config = load_config()

            yield Static(t("settings.deepseek_section"), classes="section-title")
            yield Static(t("settings.deepseek_hint"), classes="section-hint")

            with Horizontal(classes="form-row"):
                yield Static(t("settings.api_key"), classes="form-label")
                yield Input(
                    value=config["deepseek"]["api_key"],
                    placeholder="sk-...",
                    id="ds-key",
                    password=True,
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.api_url"), classes="form-label")
                yield Input(
                    value=config["deepseek"]["api_url"],
                    placeholder="https://api.deepseek.com/v1/chat/completions",
                    id="ds-url",
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.model_name"), classes="form-label")
                yield Input(
                    value=config["deepseek"]["model"],
                    placeholder="deepseek-chat",
                    id="ds-model",
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.temperature"), classes="form-label")
                yield Input(
                    value=str(config["deepseek"]["temperature"]),
                    placeholder="0.7",
                    id="ds-temp",
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.max_tokens"), classes="form-label")
                yield Input(
                    value=str(config["deepseek"]["max_tokens"]),
                    placeholder="500",
                    id="ds-tokens",
                )

            yield Static(t("settings.claude_section"), classes="section-title")
            yield Static(t("settings.claude_hint"), classes="section-hint")

            with Horizontal(classes="form-row"):
                yield Static(t("settings.api_key"), classes="form-label")
                yield Input(
                    value=config["claude"]["api_key"],
                    placeholder="sk-ant-...",
                    id="claude-key",
                    password=True,
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.api_url"), classes="form-label")
                yield Input(
                    value=config["claude"]["api_url"],
                    placeholder="https://api.anthropic.com/v1/messages",
                    id="claude-url",
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.model_name"), classes="form-label")
                yield Input(
                    value=config["claude"]["model"],
                    placeholder="claude-sonnet-4-20250514",
                    id="claude-model",
                )

            with Horizontal(classes="form-row"):
                yield Static(t("settings.max_tokens"), classes="form-label")
                yield Input(
                    value=str(config["claude"]["max_tokens"]),
                    placeholder="1500",
                    id="claude-tokens",
                )

            yield Static(t("settings.status_section"), classes="section-title")

            status = is_configured()
            ds_status = t("settings.status_configured") if status["deepseek"] else t("settings.status_not_configured")
            claude_status = t("settings.status_configured") if status["claude"] else t("settings.status_not_configured")

            with Horizontal(classes="status-row"):
                yield Static("DeepSeek:", classes="status-label")
                yield Static(ds_status, classes="status-value", id="ds-status")

            with Horizontal(classes="status-row"):
                yield Static("Claude:", classes="status-label")
                yield Static(claude_status, classes="status-value", id="claude-status")

            yield Static(t("settings.single_model_section"), classes="section-title")
            yield Static(t("settings.single_model_hint"), classes="section-hint")
            yield Checkbox(
                value=config.get("system", {}).get("single_model_mode", False),
                label=t("settings.single_model_label"),
                id="single-mode",
            )

            with Horizontal(id="btn-row"):
                yield Button(t("settings.save_btn"), variant="success", id="save-btn")
                yield Button(t("settings.back_btn"), variant="default", id="back-btn")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "back-btn":
            self.action_go_back()

    def action_save(self) -> None:
        config = load_config()

        config["deepseek"]["api_key"] = self.query_one("#ds-key", Input).value
        config["deepseek"]["api_url"] = self.query_one("#ds-url", Input).value or config["deepseek"]["api_url"]
        config["deepseek"]["model"] = self.query_one("#ds-model", Input).value or config["deepseek"]["model"]

        try:
            config["deepseek"]["temperature"] = float(self.query_one("#ds-temp", Input).value or 0.7)
        except ValueError:
            config["deepseek"]["temperature"] = 0.7

        try:
            config["deepseek"]["max_tokens"] = int(self.query_one("#ds-tokens", Input).value or 500)
        except ValueError:
            config["deepseek"]["max_tokens"] = 500

        config["claude"]["api_key"] = self.query_one("#claude-key", Input).value
        config["claude"]["api_url"] = self.query_one("#claude-url", Input).value or config["claude"]["api_url"]
        config["claude"]["model"] = self.query_one("#claude-model", Input).value or config["claude"]["model"]

        try:
            config["claude"]["max_tokens"] = int(self.query_one("#claude-tokens", Input).value or 1500)
        except ValueError:
            config["claude"]["max_tokens"] = 1500

        config.setdefault("system", {})
        config["system"]["single_model_mode"] = self.query_one("#single-mode", Checkbox).value

        save_config(config)

        status = is_configured()
        self.query_one("#ds-status", Static).update(t("settings.status_configured") if status["deepseek"] else t("settings.status_not_configured"))
        self.query_one("#claude-status", Static).update(t("settings.status_configured") if status["claude"] else t("settings.status_not_configured"))

        self.notify(t("settings.saved_notify"), severity="information")

    def action_go_back(self) -> None:
        self.app.pop_screen()
