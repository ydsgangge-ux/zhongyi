from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel
from ..i18n import t


class ChatMessage(Static):
    CSS = """
    ChatMessage {
        margin: 0 0 1 0;
        padding: 0;
        height: auto;
    }
    """

    def __init__(self, role: str, content: str):
        self.role = role
        self._msg_content = content
        super().__init__(self._render_message())

    def _render_message(self) -> str:
        if self.role == "assistant":
            return f"[bold green]🧑‍⚕️ {t('chat.assistant')}[/]\n{self._escape(self._msg_content)}"
        elif self.role == "user":
            return f"[bold blue]👤 {t('chat.user')}[/]\n{self._escape(self._msg_content)}"
        else:
            return f"[dim italic]ℹ️ {self._escape(self._msg_content)}[/]"

    def _escape(self, text: str) -> str:
        return text.replace("[", "\\[").replace("]", "\\]")
