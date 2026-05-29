from textual.screen import Screen
from textual.containers import VerticalScroll, Container
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.box import ROUNDED
from ..i18n import t


class ResultScreen(Screen):
    CSS = """
    ResultScreen {
        layout: vertical;
    }
    #result-header {
        dock: top;
        height: 3;
        padding: 0 1;
        background: $primary;
        color: $text;
        content-align: center middle;
    }
    #result-content {
        height: 1fr;
        padding: 1 2;
        scrollbar-size: 1 1;
    }
    #result-actions {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $primary;
    }
    """

    BINDINGS = [
        Binding("r", "restart", t("binding.restart"), show=True),
        Binding("q", "quit", t("binding.quit"), show=True),
    ]

    def __init__(self, result: dict):
        super().__init__()
        self.result = result

    def compose(self):
        yield Header()
        yield Static(t("result.title"), id="result-header")
        with VerticalScroll(id="result-content"):
            yield Static(self._build_result_text())
        with Container(id="result-actions"):
            yield Button(t("result.restart_btn"), variant="success", id="restart-btn")
            yield Button(t("result.quit_btn"), variant="error", id="quit-btn")
        yield Footer()

    def _build_result_text(self) -> str:
        tcm = self.result.get("tcm_analysis", {})
        western = self.result.get("western_reference", {})
        disclaimer = self.result.get("disclaimer", "")

        lines = []

        confidence = tcm.get("confidence_level", "red")
        conf_map = {"green": "result.confidence_high", "yellow": "result.confidence_medium", "red": "result.confidence_low"}
        conf_label = t(conf_map.get(confidence, "result.confidence_low"))
        lines.append(t("result.tcm_section"))
        lines.append("")

        syndrome = tcm.get("syndrome", {})
        lines.append(t("result.syndrome_title"))
        lines.append(t("result.syndrome_primary").format(value=syndrome.get('primary', '-')))
        if syndrome.get("secondary"):
            lines.append(t("result.syndrome_secondary").format(value=syndrome['secondary']))
        lines.append(t("result.confidence_label").format(conf=conf_label, pct=f"{syndrome.get('confidence', 0):.0f}"))
        lines.append("")

        bagang = tcm.get("bagang", {})
        lines.append(t("result.bagang_title"))
        lines.append(t("result.bagang_detail").format(
            yin_yang=bagang.get('yin_yang', '-'),
            biao_li=bagang.get('biao_li', '-'),
            han_re=bagang.get('han_re', '-'),
            xu_shi=bagang.get('xu_shi', '-'),
        ))
        lines.append("")

        lines.append(t("result.zangfu").format(value=tcm.get('zangfu', '-')))
        lines.append("")

        if tcm.get("special_system"):
            lines.append(t("result.special_system").format(value=tcm['special_system']))
            lines.append("")

        lines.append(t("result.etiology_title"))
        lines.append(f"  {tcm.get('etiology', '-')}")
        lines.append("")

        lines.append(t("result.treatment_title").format(value=tcm.get('treatment_principle', '-')))
        lines.append("")

        prescription = tcm.get("prescription", {})
        lines.append(t("result.plan_section"))
        lines.append("")

        if prescription.get("diet_therapy"):
            lines.append(t("result.diet_therapy"))
            lines.append(f"  {prescription['diet_therapy']}")
            lines.append("")

        if prescription.get("patent_medicine"):
            lines.append(t("result.patent_medicine"))
            lines.append(f"  {prescription['patent_medicine']}")
            lines.append("")

        if prescription.get("decoction"):
            lines.append(t("result.decoction"))
            lines.append(f"  {prescription['decoction']}")
            lines.append(t("result.decoction_warning"))
            lines.append("")

        if prescription.get("warning"):
            lines.append(t("result.warning"))
            lines.append(f"  {prescription['warning']}")
            lines.append("")

        lifestyle = tcm.get("lifestyle", {})
        if any(lifestyle.values()):
            lines.append(t("result.lifestyle_section"))
            lines.append("")
            if lifestyle.get("diet"):
                lines.append(t("result.lifestyle_diet").format(value=lifestyle['diet']))
            if lifestyle.get("sleep"):
                lines.append(t("result.lifestyle_sleep").format(value=lifestyle['sleep']))
            if lifestyle.get("emotion"):
                lines.append(t("result.lifestyle_emotion").format(value=lifestyle['emotion']))
            lines.append("")

        danger_signals = western.get("danger_signals", [])
        possible_conditions = western.get("possible_conditions", [])
        recommended_tests = western.get("recommended_tests", [])
        doctor_visit = western.get("doctor_visit", {})

        if any([danger_signals, possible_conditions, recommended_tests, doctor_visit]):
            lines.append(t("result.western_section"))
            lines.append("")

            if danger_signals:
                lines.append(t("result.danger_signals"))
                for sig in danger_signals:
                    lines.append(f"  [{sig.get('urgency', 'high')}] {sig.get('signal', '')} — {sig.get('action', '')}")
                lines.append("")

            if possible_conditions:
                lines.append(t("result.possible_conditions"))
                prob_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                for cond in possible_conditions:
                    prob = cond.get("probability", "low")
                    prob_icon = prob_icons.get(prob, "⚪")
                    lines.append(f"  {prob_icon} {cond.get('condition', '')}：{cond.get('description', '')}")
                lines.append("")

            if recommended_tests:
                lines.append(t("result.recommended_tests"))
                for test in recommended_tests:
                    lines.append(f"  📋 {test.get('test', '')} — {test.get('reason', '')}")
                lines.append("")

            if doctor_visit:
                lines.append(t("result.doctor_visit"))
                if doctor_visit.get("needed"):
                    urgency = doctor_visit.get("urgency", "routine")
                    urg_keys = {"immediate": "result.urgency_immediate", "soon": "result.urgency_soon", "routine": "result.urgency_routine"}
                    urg_label = t(urg_keys.get(urgency, "result.urgency_routine"))
                    lines.append(t("result.department_format").format(urg=urg_label, dept=doctor_visit.get('department', '-')))
                else:
                    lines.append(t("result.no_emergency_need"))
                lines.append("")

        lines.append(t("result.disclaimer_section"))
        lines.append(f"[italic yellow]{disclaimer}[/]")

        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "restart-btn":
            self.app.restart()
        elif event.button.id == "quit-btn":
            self.app.exit()
