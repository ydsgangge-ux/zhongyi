from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button, Input, Select
from textual.binding import Binding
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.box import ROUNDED
from ..i18n import t


class WelcomeScreen(Screen):
    CSS = """
    WelcomeScreen {
        align: center middle;
    }
    #welcome-container {
        width: 60;
        height: auto;
        padding: 2 4;
        border: round $primary;
        background: $surface;
    }
    #title {
        text-align: center;
        margin-bottom: 1;
    }
    #subtitle {
        text-align: center;
        margin-bottom: 1;
        color: $text-muted;
    }
    #disclaimer {
        text-align: center;
        margin-top: 1;
        color: $warning;
        text-style: italic;
    }
    .form-row {
        height: 3;
        margin-bottom: 1;
    }
    .form-label {
        width: 10;
        padding: 1 1 0 0;
        color: $text-muted;
    }
    .form-input {
        width: 1fr;
    }
    #start-btn {
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("enter", "start", t("binding.start"), show=False),
    ]

    def compose(self):
        yield Header()
        with Container(id="welcome-container"):
            yield Static(Text(t("welcome.title"), style="bold green", justify="center"), id="title")
            yield Static(t("welcome.subtitle"), id="subtitle")
            yield Static("")

            with Horizontal(classes="form-row"):
                yield Static(t("welcome.age"), classes="form-label")
                yield Input(placeholder=t("welcome.age_placeholder"), id="age-input", max_length=3)

            with Horizontal(classes="form-row"):
                yield Static(t("welcome.gender"), classes="form-label")
                yield Select(
                    [(t("welcome.gender_select"), ""), (t("welcome.gender_male"), "male"), (t("welcome.gender_female"), "female")],
                    id="gender-select",
                    value="",
                )

            with Horizontal(classes="form-row"):
                yield Static(t("welcome.region"), classes="form-label")
                yield Input(placeholder=t("welcome.region_placeholder"), id="region-input")

            yield Button(t("welcome.start_btn"), variant="success", id="start-btn")
            yield Static(
                t("welcome.disclaimer"),
                id="disclaimer",
            )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.action_start()

    def action_start(self) -> None:
        age_str = self.query_one("#age-input", Input).value
        gender_raw = self.query_one("#gender-select", Select).value
        region = self.query_one("#region-input", Input).value

        try:
            age = int(age_str) if age_str else None
        except ValueError:
            age = None

        from textual.widgets import Select as _Select
        if gender_raw is _Select.NULL or not gender_raw:
            gender = None
        else:
            gender = str(gender_raw)

        session_data = {
            "age": age,
            "gender": gender,
            "region": region if region else None,
        }
        self.app.start_inquiry(session_data)
