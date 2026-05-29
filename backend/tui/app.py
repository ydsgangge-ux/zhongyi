import traceback
from textual.app import App, ComposeResult
from textual.binding import Binding
from .screens.welcome import WelcomeScreen
from .screens.inquiry import InquiryScreen
from .screens.result import ResultScreen
from .screens.settings import SettingsScreen
from .i18n import t as _t


class TCMApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    """

    TITLE = "TCM AI Health Advisor"
    SUB_TITLE = "TCM AI Health Advisor"

    BINDINGS = [
        Binding("s", "show_settings", _t("binding.settings"), show=True),
        Binding("q", "quit", _t("binding.quit"), show=True),
        Binding("l", "toggle_lang", "Lang", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.session_data = {}

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

    def start_inquiry(self, session_data: dict) -> None:
        self.session_data = session_data
        try:
            self.push_screen(InquiryScreen(session_data))
        except Exception as e:
            traceback.print_exc()
            self._show_error(_t("error.nav_inquiry_failed") + str(e))

    def show_result(self, result: dict) -> None:
        try:
            self.push_screen(ResultScreen(result))
        except Exception as e:
            traceback.print_exc()
            self._show_error(_t("error.nav_result_failed") + str(e))

    def action_show_settings(self) -> None:
        try:
            self.push_screen(SettingsScreen())
        except Exception as e:
            traceback.print_exc()
            self._show_error(_t("error.settings_failed") + str(e))

    def action_toggle_lang(self) -> None:
        from .i18n import get_locale, set_locale
        current = get_locale()
        new = "en" if current == "zh" else "zh"
        set_locale(new)
        self.restart()

    def _show_error(self, message: str) -> None:
        from textual.widgets import Static
        from textual.containers import Container
        from textual.screen import Screen
        from .i18n import t as _tt

        class ErrorScreen(Screen):
            CSS = """
            ErrorScreen { align: center middle; }
            #error-box {
                width: 60;
                padding: 2 4;
                border: round $error;
                background: $surface;
            }
            #error-msg { color: $error; margin-bottom: 1; }
            """
            def __init__(self, msg):
                self._msg = msg
                super().__init__()
            def compose(self):
                with Container(id="error-box"):
                    yield Static(_tt("error.title"), id="error-msg")
                    yield Static(self._msg)
                    yield Static(_tt("error.press_esc"))

            BINDINGS = [Binding("escape", "go_back", _tt("binding.back"), show=True)]

            def action_go_back(self):
                self.app.pop_screen()

        self.push_screen(ErrorScreen(message))

    def restart(self) -> None:
        self.session_data = {}
        self.pop_screen()
        while len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(WelcomeScreen())


if __name__ == "__main__":
    app = TCMApp()
    app.run()
