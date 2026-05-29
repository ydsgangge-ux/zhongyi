import json
import os
from typing import Optional

from .gender_differentiation import HERB_CATEGORIES, FEMALE_SAFETY_MODES, MALE_SAFETY_HERBS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

TOXIC_HERBS = [
    "附子", "川乌", "草乌", "马钱子", "斑蝥", "蟾酥",
    "砒霜", "雄黄", "轻粉", "红粉", "白降丹",
    "洋金花", "闹羊花", "雪上一枝蒿", "天南星",
]

PREGNANCY_FORBIDDEN = [
    "麝香", "三棱", "莪术", "水蛭", "虻虫", "斑蝥",
    "川乌", "草乌", "附子", "天南星", "马钱子",
    "土鳖虫", "蜈蚣", "全蝎", "轻粉", "雄黄",
]

PREGNANCY_CAUTION = [
    "桃仁", "红花", "牛膝", "川芎", "大黄", "枳实",
    "芒硝", "番泻叶", "芦荟", "甘遂", "大戟", "芫花", "牵牛", "巴豆",
]

LACTATION_FORBIDDEN = [
    "麦芽",
]

MALE_REPRODUCTIVE_HARMS = [
    "雷公藤", "棉花根",
]


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

    def check_gender_safety(self, herbs_text: str, session: dict = None) -> dict:
        warnings = []
        if not session:
            return {"safe": True, "warnings": []}

        gender = session.get("gender", "")
        pregnancy = session.get("pregnancy_status")
        menstrual = session.get("menstrual_data") or {}
        fertility_need = session.get("male_fertility_need", False)

        if gender == "女":
            if pregnancy in ("pregnant_early", "pregnant_late"):
                for herb in PREGNANCY_FORBIDDEN:
                    if herb in herbs_text:
                        warnings.append(f"妊娠禁用：{herb}")
                for herb in PREGNANCY_CAUTION:
                    if herb in herbs_text:
                        warnings.append(f"妊娠慎用：{herb}")

            if pregnancy == "planning_pregnancy":
                blood_herbs = HERB_CATEGORIES.get("blood_activating", []) + HERB_CATEGORIES.get("blood_breaking", [])
                for herb in blood_herbs:
                    if herb in herbs_text:
                        warnings.append(f"备孕期慎用（活血）：{herb}")

            if pregnancy == "breastfeeding":
                for herb in LACTATION_FORBIDDEN:
                    if herb in herbs_text:
                        warnings.append(f"哺乳期禁用：{herb}")

            if menstrual.get("is_menstruating"):
                flow = menstrual.get("flow", "")
                color = menstrual.get("color", "")
                if flow in ("多", "heavy"):
                    blood_activating = HERB_CATEGORIES.get("blood_activating", [])
                    for herb in blood_activating:
                        if herb in herbs_text:
                            warnings.append(f"经期量多慎用（活血）：{herb}")

        if gender == "男" and fertility_need:
            for herb in MALE_REPRODUCTIVE_HARMS:
                if herb in herbs_text:
                    warnings.append(f"有生育需求慎用：{herb}（可能影响生殖功能）")

        return {
            "safe": len(warnings) == 0,
            "warnings": warnings,
        }

    def check_danger_signals(self, message: str) -> dict:
        matched = []
        if not self.danger_signals:
            return {"dangerous": False, "matched": [], "warning": ""}

        for category, signals in self.danger_signals.get("categories", {}).items():
            for signal in signals:
                keywords = signal.get("keywords", [])
                for keyword in keywords:
                    if keyword in message:
                        matched.append({
                            "category": category,
                            "signal": signal.get("name", ""),
                            "action": signal.get("action", "请立即就医"),
                            "urgency": signal.get("urgency", "high"),
                        })
                        break

        if matched:
            warning_parts = ["🚨 检测到危险信号！\n"]
            for m in matched:
                warning_parts.append(f"• {m['signal']}（{m['category']}）— {m['action']}")
            warning_parts.append("\n⚠️ 请立即就医，不要延误！本系统不对急症提供辨证建议。")
            return {
                "dangerous": True,
                "matched": matched,
                "warning": "\n".join(warning_parts),
            }

        return {"dangerous": False, "matched": [], "warning": ""}

    def check_herb_conflicts(self, prescription: dict) -> dict:
        conflicts = []
        all_herbs = []

        decoction = prescription.get("decoction", "")
        patent = prescription.get("patent_medicine", "")
        all_herbs_text = f"{decoction} {patent}"

        for herb in TOXIC_HERBS:
            if herb in all_herbs_text:
                conflicts.append({
                    "type": "toxic_herb",
                    "herb": herb,
                    "rule": "毒性药材禁止出现在推荐处方",
                })

        if self.herb_conflicts:
            for conflict in self.herb_conflicts.get("eighteen_contraries", []):
                herb1 = conflict.get("herb1", "")
                herb2 = conflict.get("herb2", "")
                if herb1 in all_herbs_text and herb2 in all_herbs_text:
                    conflicts.append({
                        "type": "eighteen_contraries",
                        "herb1": herb1,
                        "herb2": herb2,
                        "rule": conflict.get("rule", "十八反"),
                    })

            for conflict in self.herb_conflicts.get("nineteen_mutual_antagonisms", []):
                herb1 = conflict.get("herb1", "")
                herb2 = conflict.get("herb2", "")
                if herb1 in all_herbs_text and herb2 in all_herbs_text:
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
