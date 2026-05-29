import asyncio
import json
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal, Container
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding
from textual.worker import Worker, get_current_worker
from rich.text import Text
from rich.markup import escape
from ...core.inquiry_engine import InquiryEngine
from ...core.tcm_engine import TCMEngine
from ...core.western_engine import WesternEngine
from ...core.safety_guard import SafetyGuard
from ..widgets.chat_message import ChatMessage
from ..i18n import t


class InquiryScreen(Screen):
    CSS = """
    InquiryScreen {
        layout: vertical;
    }
    #chat-header {
        dock: top;
        height: 3;
        padding: 0 1;
        background: $primary;
        color: $text;
        content-align: center middle;
    }
    #chat-messages {
        height: 1fr;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    #danger-alert {
        dock: top;
        height: auto;
        padding: 1 2;
        background: $error;
        color: white;
        text-style: bold;
        display: none;
    }
    #chat-input-area {
        dock: bottom;
        height: auto;
        padding: 1;
        background: $surface;
        border-top: solid $primary;
    }
    #chat-input {
        width: 1fr;
    }
    #input-row {
        height: 3;
    }
    #action-row {
        height: 3;
        margin-top: 1;
    }
    #analyze-btn {
        margin-right: 1;
    }
    """

    BINDINGS = [
        Binding("enter", "send_message", t("binding.send"), show=False),
        Binding("ctrl+a", "analyze", t("binding.analyze"), show=True),
    ]

    def __init__(self, session_data: dict):
        super().__init__()
        self.session_data = session_data
        self.engine = InquiryEngine()
        self.tcm_engine = TCMEngine()
        self.western_engine = WesternEngine()
        self.safety_guard = SafetyGuard()
        self.session = None
        self.current_round = 0
        self.is_streaming = False
        self.danger_signal = None

    def compose(self):
        yield Header()
        yield Static(t("inquiry.header"), id="chat-header")
        yield Static("", id="danger-alert")
        with VerticalScroll(id="chat-messages"):
            pass
        with Container(id="chat-input-area"):
            with Horizontal(id="input-row"):
                yield Input(placeholder=t("inquiry.input_placeholder"), id="chat-input")
                yield Button(t("inquiry.send_btn"), variant="primary", id="send-btn")
            with Horizontal(id="action-row"):
                yield Button(t("inquiry.analyze_btn"), variant="success", id="analyze-btn")
                yield Button(t("inquiry.restart_btn"), variant="default", id="restart-btn")
        yield Footer()

    def on_mount(self) -> None:
        from ..i18n import get_locale
        locale = get_locale()
        season = self.engine.get_current_season()
        self.session = self.engine.create_session(
            session_id="tui-session",
            region=self.session_data.get("region"),
            age=self.session_data.get("age"),
            gender=self.session_data.get("gender"),
            season=season,
            locale=locale,
        )
        self.add_system_message(t("inquiry.season_prefix") + season)
        self.add_assistant_message(t("inquiry.greeting"))

    def add_assistant_message(self, text: str) -> None:
        messages = self.query_one("#chat-messages")
        msg = ChatMessage("assistant", text)
        messages.mount(msg)
        messages.scroll_end(animate=False)

    def add_user_message(self, text: str) -> None:
        messages = self.query_one("#chat-messages")
        msg = ChatMessage("user", text)
        messages.mount(msg)
        messages.scroll_end(animate=False)

    def add_system_message(self, text: str) -> None:
        messages = self.query_one("#chat-messages")
        msg = ChatMessage("system", text)
        messages.mount(msg)
        messages.scroll_end(animate=False)

    def show_danger(self, text: str) -> None:
        alert = self.query_one("#danger-alert")
        alert.update(f"🚨 {text}")
        alert.styles.display = "block"
        self.danger_signal = text

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.action_send_message()
        elif event.button.id == "analyze-btn":
            self.action_analyze()
        elif event.button.id == "restart-btn":
            self.app.restart()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            self.action_send_message()

    def action_send_message(self) -> None:
        if self.is_streaming or self.danger_signal:
            return
        input_widget = self.query_one("#chat-input", Input)
        text = input_widget.value.strip()
        if not text:
            return

        input_widget.value = ""
        self.add_user_message(text)

        danger_check = self.safety_guard.check_danger_signals(text)
        if danger_check["dangerous"]:
            self.show_danger(danger_check["warning"])
            self.add_system_message(t("inquiry.danger_detected"))
            return

        self.session["messages"].append({"role": "user", "content": text})
        self.is_streaming = True
        self.run_worker(self._stream_response(text), exclusive=True)

    async def _stream_response(self, user_message: str):
        full_response = ""
        try:
            async for chunk in self.engine.process_message(self.session, user_message):
                full_response += chunk
        except Exception as e:
            full_response = t("inquiry.request_failed").format(e)

        self.current_round = self.session["round"]
        self.add_assistant_message(full_response if full_response else t("inquiry.no_reply"))
        self.is_streaming = False

        if self.current_round >= 5:
            self.add_system_message(t("inquiry.rounds_complete"))

    def action_analyze(self) -> None:
        if self.is_streaming or self.danger_signal:
            return
        if self.current_round < 3:
            self.add_system_message(t("inquiry.rounds_insufficient"))
            return
        self.add_system_message(t("inquiry.analyzing"))
        self.run_worker(self._do_analysis(), exclusive=True)

    async def _do_analysis(self):
        try:
            tcm_result = await self.tcm_engine.analyze(self.session)
            western_result = await self.western_engine.analyze(self.session)

            herb_check = self.safety_guard.check_herb_conflicts(tcm_result.get("prescription", {}))
            if herb_check["has_conflict"]:
                tcm_result["prescription"]["warning"] = herb_check["warning"]

            result = {
                "tcm_analysis": tcm_result,
                "western_reference": western_result,
                "disclaimer": t("inquiry.disclaimer_text"),
            }
            self.app.show_result(result)
        except Exception as e:
            self.add_system_message(t("inquiry.analyze_failed").format(e))
