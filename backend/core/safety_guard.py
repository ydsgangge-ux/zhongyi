import json
import os
import re
from typing import Optional

from .gender_differentiation import HERB_CATEGORIES, MALE_SAFETY_HERBS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

TOXIC_HERBS = [
    "附子", "川乌", "草乌", "马钱子", "斑蝥", "蟾酥",
    "砒霜", "雄黄", "轻粉", "红粉", "白降丹",
    "洋金花", "闹羊花", "雪上一枝蒿", "天南星",
]

# 与 gender_differentiation 共用同一份分类，避免两处清单失同步
PREGNANCY_FORBIDDEN = HERB_CATEGORIES.get("pregnancy_contraindicated", [])

PREGNANCY_CAUTION = list(dict.fromkeys(
    HERB_CATEGORIES.get("blood_activating", [])
    + HERB_CATEGORIES.get("blood_breaking", [])
    + ["大黄", "枳实", "芒硝", "番泻叶", "芦荟", "甘遂", "大戟", "芫花", "牵牛", "巴豆"]
))

LACTATION_FORBIDDEN = ["麦芽"]

MALE_REPRODUCTIVE_HARMS = MALE_SAFETY_HERBS

# "烧到39.8度""体温40℃""fever 39.6" 这类数值型高热，关键词表覆盖不全
HIGH_FEVER_PATTERN = re.compile(r"(3[9]\.[5-9]|4[0-2](?:\.\d+)?)\s*(?:度|℃|°C|°c|degrees?)")

# LLM 常在处方后写"方中不含附子、川乌"这类否定说明，不应被判为使用了毒性药材
_NEGATED_CLAUSE = re.compile(
    r"[^，。；\n]*(?:不含|不包含|未使用|未用|禁用|避免|禁止|忌用|不可用|不宜)[^，。；\n]*[，。；]?"
)


def _strip_negated(text: str) -> str:
    return _NEGATED_CLAUSE.sub("", text)


def _herb_present(text: str, herb: str) -> bool:
    """白附子与附子是不同药材，子串匹配需要排除误伤。"""
    if herb == "附子":
        return "附子" in text.replace("白附子", "")
    return herb in text


class SafetyGuard:
    def __init__(self):
        self.danger_signals = self._load_json("danger_signals.json")
        self.herb_conflicts = self._load_json("herb_conflicts.json")

    def _load_json(self, filename: str) -> dict:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def check_gender_safety(self, herbs_text: str, session: dict = None, locale: str = "zh") -> dict:
        warnings = []
        if not session:
            return {"safe": True, "warnings": []}

        en = locale == "en"
        gender = session.get("gender", "")
        pregnancy = session.get("pregnancy_status")
        menstrual = session.get("menstrual_data") or {}
        fertility_need = session.get("male_fertility_need", False)
        herbs_text = _strip_negated(herbs_text or "")

        if gender == "女":
            if pregnancy in ("pregnant_early", "pregnant_late"):
                for herb in PREGNANCY_FORBIDDEN:
                    if _herb_present(herbs_text, herb):
                        warnings.append(
                            f"Contraindicated in pregnancy: {herb}" if en else f"妊娠禁用：{herb}"
                        )
                for herb in PREGNANCY_CAUTION:
                    if _herb_present(herbs_text, herb):
                        warnings.append(
                            f"Use with caution in pregnancy: {herb}" if en else f"妊娠慎用：{herb}"
                        )

            if pregnancy == "planning_pregnancy":
                blood_herbs = HERB_CATEGORIES.get("blood_activating", []) + HERB_CATEGORIES.get("blood_breaking", [])
                for herb in blood_herbs:
                    if _herb_present(herbs_text, herb):
                        warnings.append(
                            f"Avoid when trying to conceive (blood-activating): {herb}"
                            if en else f"备孕期慎用（活血）：{herb}"
                        )

            if pregnancy == "breastfeeding":
                for herb in LACTATION_FORBIDDEN:
                    if _herb_present(herbs_text, herb):
                        warnings.append(
                            f"Contraindicated while breastfeeding: {herb}"
                            if en else f"哺乳期禁用：{herb}"
                        )

            if menstrual.get("is_menstruating"):
                flow = menstrual.get("flow", "")
                if flow in ("多", "heavy"):
                    for herb in HERB_CATEGORIES.get("blood_activating", []):
                        if _herb_present(herbs_text, herb):
                            warnings.append(
                                f"Avoid during heavy menstruation (blood-activating): {herb}"
                                if en else f"经期量多慎用（活血）：{herb}"
                            )

        if gender == "男" and fertility_need:
            for herb in MALE_REPRODUCTIVE_HARMS:
                if _herb_present(herbs_text, herb):
                    warnings.append(
                        f"Avoid if fertility is desired: {herb} (may impair reproductive function)"
                        if en else f"有生育需求慎用：{herb}（可能影响生殖功能）"
                    )

        return {
            "safe": len(warnings) == 0,
            "warnings": warnings,
        }

    def check_danger_signals(self, message: str, locale: str = "zh") -> dict:
        matched = []
        user_text = message or ""
        lowered = user_text.lower()
        en = locale == "en"

        for category, signals in self.danger_signals.get("categories", {}).items():
            for signal in signals:
                for keyword in signal.get("keywords", []):
                    haystack = lowered if keyword.isascii() else user_text
                    if keyword.lower() in haystack:
                        matched.append({
                            "category": category,
                            "signal": signal.get("name_en" if en else "name", ""),
                            "action": signal.get("action_en" if en else "action", ""),
                            "urgency": signal.get("urgency", "high"),
                        })
                        break

        if HIGH_FEVER_PATTERN.search(user_text):
            fear_names = {m["signal"] for m in matched}
            fever_name = "High fever above 39.5°C" if en else "高热39.5℃以上"
            if fever_name not in fear_names:
                matched.append({
                    "category": "Respiratory / Digestive / Other" if en else "呼吸/消化/其他",
                    "signal": fever_name,
                    "action": "Seek medical care immediately; the cause of the high fever needs investigation."
                    if en else "请立即就医，高热需查明原因",
                    "urgency": "high",
                })

        if not matched:
            return {"dangerous": False, "matched": [], "warning": ""}

        if en:
            parts = ["🚨 Danger signal detected!\n"]
            for m in matched:
                parts.append(f"• {m['signal']} ({m['category']}) — {m['action']}")
            parts.append("\n⚠️ Please seek immediate medical attention. This system does not provide TCM advice for emergencies.")
            warning = "\n".join(parts)
        else:
            parts = ["🚨 检测到危险信号！\n"]
            for m in matched:
                parts.append(f"• {m['signal']}（{m['category']}）— {m['action']}")
            parts.append("\n⚠️ 请立即就医，不要延误！本系统不对急症提供辨证建议。")
            warning = "\n".join(parts)

        return {"dangerous": True, "matched": matched, "warning": warning}

    def check_herb_conflicts(self, prescription: dict) -> dict:
        conflicts = []

        decoction = prescription.get("decoction", "")
        patent = prescription.get("patent_medicine", "")
        all_herbs_text = _strip_negated(f"{decoction} {patent}")

        for herb in TOXIC_HERBS:
            if _herb_present(all_herbs_text, herb):
                conflicts.append({
                    "type": "toxic_herb",
                    "herb": herb,
                    "rule": "毒性药材禁止出现在推荐处方",
                })

        if self.herb_conflicts:
            for conflict in self.herb_conflicts.get("eighteen_contraries", []):
                herb1 = conflict.get("herb1", "")
                herb2 = conflict.get("herb2", "")
                if _herb_present(all_herbs_text, herb1) and _herb_present(all_herbs_text, herb2):
                    conflicts.append({
                        "type": "eighteen_contraries",
                        "herb1": herb1,
                        "herb2": herb2,
                        "rule": conflict.get("rule", "十八反"),
                    })

            for conflict in self.herb_conflicts.get("nineteen_mutual_antagonisms", []):
                herb1 = conflict.get("herb1", "")
                herb2 = conflict.get("herb2", "")
                if _herb_present(all_herbs_text, herb1) and _herb_present(all_herbs_text, herb2):
                    conflicts.append({
                        "type": "nineteen_mutual_antagonisms",
                        "herb1": herb1,
                        "herb2": herb2,
                        "rule": conflict.get("rule", "十九畏"),
                    })

        if conflicts:
            warning_parts = ["⚠️ 配伍安全检查发现问题：\n"]
            for c in conflicts:
                if c["type"] == "toxic_herb":
                    warning_parts.append(f"• 毒性药材「{c['herb']}」禁止推荐")
                elif c["type"] == "eighteen_contraries":
                    warning_parts.append(f"• 十八反：「{c['herb1']}」与「{c['herb2']}」相反")
                elif c["type"] == "nineteen_mutual_antagonisms":
                    warning_parts.append(f"• 十九畏：「{c['herb1']}」与「{c['herb2']}」相畏")
            return {"has_conflict": True, "conflicts": conflicts, "warning": "\n".join(warning_parts)}

        return {"has_conflict": False, "conflicts": [], "warning": ""}

    def check_minor(self, age: Optional[int]) -> bool:
        if age is not None and age < 18:
            return True
        return False
