from datetime import datetime


def calc_physiological_stage(gender: str, birth_year: int = None) -> str:
    if not birth_year or not gender:
        return None

    age = datetime.now().year - birth_year
    if age < 0:
        age = 0

    if gender == "女":
        if age <= 18:
            return "adolescent"
        elif age <= 45:
            return "reproductive"
        elif age <= 55:
            return "perimenopausal"
        else:
            return "elderly_female"
    elif gender == "男":
        if age <= 40:
            return "young_male"
        elif age <= 55:
            return "middle_male"
        else:
            return "elderly_male"
    return None


STAGE_LABELS = {
    "zh": {
        "adolescent": "青春期",
        "reproductive": "育龄期",
        "perimenopausal": "围绝经期",
        "elderly_female": "老年期（女）",
        "young_male": "青壮年",
        "middle_male": "中年",
        "elderly_male": "老年期（男）",
    },
    "en": {
        "adolescent": "Adolescent",
        "reproductive": "Reproductive Age",
        "perimenopausal": "Perimenopausal",
        "elderly_female": "Elderly (Female)",
        "young_male": "Young Adult (Male)",
        "middle_male": "Middle Age (Male)",
        "elderly_male": "Elderly (Male)",
    },
}


FEMALE_TCM_WEIGHT_BIAS = {
    "reproductive": {
        "blood_deficiency": 0.20,
        "blood_stasis": 0.20,
        "liver_qi_stagnation": 0.15,
        "chong_ren_disharmony": 0.10,
        "spleen_deficiency": 0.10,
    },
    "perimenopausal": {
        "kidney_yin_deficiency": 0.30,
        "yin_deficiency_fire": 0.30,
        "heart_kidney_disharmony": 0.20,
        "liver_kidney_yin_deficiency": 0.20,
    },
}

MALE_TCM_WEIGHT_BIAS = {
    "young_male": {
        "liver_qi_stagnation": 0.20,
        "damp_heat": 0.20,
        "spleen_stomach": 0.15,
    },
    "middle_male": {
        "kidney_deficiency": 0.25,
        "liver_kidney_yin_deficiency": 0.20,
        "stress_liver_kidney": 0.15,
    },
    "elderly_male": {
        "kidney_yang_deficiency": 0.25,
        "heart_qi_deficiency": 0.25,
        "phlegm_stasis": 0.15,
    },
}

FEMALE_SAFETY_MODES = {
    "planning_pregnancy": {
        "label_zh": "严格模式A（备孕中）",
        "label_en": "Strict Mode A (Planning Pregnancy)",
        "forbidden_categories": ["blood_activating", "blood_breaking", "strong_cold_harming_yang"],
        "forbidden_herbs": ["雷公藤", "棉花根"],
    },
    "pregnant_early": {
        "label_zh": "最严格模式（孕早期）",
        "label_en": "Strictest Mode (Early Pregnancy)",
        "forbidden_categories": ["pregnancy_contraindicated"],
        "forbidden_herbs": [],
    },
    "pregnant_late": {
        "label_zh": "最严格模式（孕中晚期）",
        "label_en": "Strictest Mode (Late Pregnancy)",
        "forbidden_categories": ["pregnancy_contraindicated"],
        "forbidden_herbs": [],
    },
    "breastfeeding": {
        "label_zh": "严格模式B（哺乳期）",
        "label_en": "Strict Mode B (Breastfeeding)",
        "forbidden_categories": ["bitter_cold", "strong_menstrual_moving"],
        "forbidden_herbs": ["麦芽"],
    },
    "menstrual_blood_stasis": {
        "label_zh": "注意模式（经期·血瘀型）",
        "label_en": "Caution Mode (Menstrual · Blood Stasis)",
        "forbidden_categories": ["astringent_hemostatic"],
    },
    "menstrual_heavy": {
        "label_zh": "注意模式（经期·量多型）",
        "label_en": "Caution Mode (Menstrual · Heavy Flow)",
        "forbidden_categories": ["blood_activating"],
    },
    "menstrual_normal": {
        "label_zh": "注意模式（经期·一般）",
        "label_en": "Caution Mode (Menstrual · Normal)",
        "forbidden_categories": ["strong_cold", "strong_purgative"],
    },
}

MALE_SAFETY_HERBS = ["雷公藤", "棉花根"]

HERB_CATEGORIES = {
    "blood_activating": ["丹参", "红花", "桃仁", "川芎", "牛膝", "益母草", "泽兰", "王不留行"],
    "blood_breaking": ["三棱", "莪术", "水蛭", "虻虫", "土鳖虫"],
    "strong_cold_harming_yang": ["芒硝", "大黄", "甘遂", "大戟", "芫花", "巴豆"],
    "pregnancy_contraindicated": [
        "巴豆", "牵牛", "大戟", "芫花", "甘遂", "商陆",
        "麝香", "三棱", "莪术", "水蛭", "虻虫", "斑蝥",
        "川乌", "草乌", "附子", "天南星", "马钱子",
        "土鳖虫", "蜈蚣", "全蝎", "轻粉", "雄黄",
    ],
    "bitter_cold": ["黄连", "黄芩", "黄柏", "龙胆草", "苦参", "栀子"],
    "strong_menstrual_moving": ["红花", "桃仁", "牛膝", "益母草"],
    "astringent_hemostatic": ["棕榈炭", "血余炭", "藕节炭", "仙鹤草", "白及"],
    "strong_cold": ["石膏", "知母", "寒水石"],
    "strong_purgative": ["大黄", "芒硝", "番泻叶", "芦荟"],
    "male_reproductive_harm": ["雷公藤", "棉花根"],
}


def get_weight_bias_context(gender: str, stage: str, locale: str = "zh") -> str:
    if not gender or not stage:
        return ""

    if gender == "女" and stage in FEMALE_TCM_WEIGHT_BIAS:
        biases = FEMALE_TCM_WEIGHT_BIAS[stage]
    elif gender == "男" and stage in MALE_TCM_WEIGHT_BIAS:
        biases = MALE_TCM_WEIGHT_BIAS[stage]
    else:
        return ""

    stage_label = STAGE_LABELS.get(locale, STAGE_LABELS["zh"]).get(stage, stage)

    if locale == "zh":
        lines = [f"\n【性别-生理阶段权重偏置】"]
        lines.append(f"用户生理阶段：{stage_label}（{gender}）")
        lines.append("以下为初始辨证权重偏置（症状证据可覆盖）：")
        bias_labels = {
            "blood_deficiency": "血虚",
            "blood_stasis": "血瘀",
            "liver_qi_stagnation": "肝气郁结",
            "chong_ren_disharmony": "冲任失调",
            "spleen_deficiency": "脾虚",
            "kidney_yin_deficiency": "肾阴虚",
            "yin_deficiency_fire": "阴虚火旺",
            "heart_kidney_disharmony": "心肾不交",
            "liver_kidney_yin_deficiency": "肝肾阴虚",
            "kidney_deficiency": "肾虚",
            "damp_heat": "湿热内蕴",
            "spleen_stomach": "脾胃问题",
            "stress_liver_kidney": "压力→肝郁→肾虚",
            "kidney_yang_deficiency": "肾阳虚",
            "heart_qi_deficiency": "心气不足",
            "phlegm_stasis": "痰瘀互结",
        }
        for key, weight in biases.items():
            label = bias_labels.get(key, key)
            lines.append(f"  {label} +{int(weight * 100)}%")
        lines.append("注意：以上为初始偏置，最终辨证以症状证据为准。")
    else:
        lines = [f"\n[Gender-Physiological Stage Weight Bias]"]
        lines.append(f"User stage: {stage_label} ({gender})")
        lines.append("Initial syndrome differentiation weight biases (overridable by symptom evidence):")
        bias_labels_en = {
            "blood_deficiency": "Blood Deficiency",
            "blood_stasis": "Blood Stasis",
            "liver_qi_stagnation": "Liver Qi Stagnation",
            "chong_ren_disharmony": "Chong-Ren Disharmony",
            "spleen_deficiency": "Spleen Deficiency",
            "kidney_yin_deficiency": "Kidney Yin Deficiency",
            "yin_deficiency_fire": "Yin Deficiency Fire",
            "heart_kidney_disharmony": "Heart-Kidney Disharmony",
            "liver_kidney_yin_deficiency": "Liver-Kidney Yin Deficiency",
            "kidney_deficiency": "Kidney Deficiency",
            "damp_heat": "Damp-Heat",
            "spleen_stomach": "Spleen-Stomach Issues",
            "stress_liver_kidney": "Stress → Liver Depression → Kidney Deficiency",
            "kidney_yang_deficiency": "Kidney Yang Deficiency",
            "heart_qi_deficiency": "Heart Qi Deficiency",
            "phlegm_stasis": "Phlegm-Stasis",
        }
        for key, weight in biases.items():
            label = bias_labels_en.get(key, key)
            lines.append(f"  {label} +{int(weight * 100)}%")
        lines.append("Note: These are initial biases; final diagnosis depends on symptom evidence.")

    return "\n".join(lines)


def get_emotional_context(gender: str, locale: str = "zh") -> str:
    if not gender:
        return ""

    if locale == "zh":
        if gender == "女":
            return """\n【情志采集（女性）】
在问诊中注意采集以下情志信息：
- 近期情绪状态（平稳/焦虑/低落/易怒/波动大）
- 情绪与月经周期的关联（经前加重/无明显关联）
- 睡眠中的梦境（多梦/噩梦/无梦）
- 有无"莫名哭泣"或"心中烦乱"感
注意：女子以血为本，情志多先伤肝血，次损冲任。请在辨证时关注肝气郁结→血虚→冲任失调的连锁路径。"""
        else:
            return """\n【情志采集（男性）】
男性情志问题常以躯体症状呈现，请关注以下代理指标：
- 睡眠质量突然下降
- 性欲明显减退
- 食欲变化（暴食或不思饮食）
- 工作效率自述下降
- 社交退缩行为描述
注意：男子以精为主，情志多先伤肝疏泄，久则累肾。如出现3项以上代理指标阳性，请在辨证报告中加入情志分析段落。"""
    else:
        if gender == "女":
            return """\n[Emotional Assessment (Female)]
Collect the following emotional information during inquiry:
- Recent emotional state (stable/anxious/depressed/irritable/fluctuating)
- Association between emotions and menstrual cycle (worse before period/no clear link)
- Dream patterns (frequent dreams/nightmares/dreamless)
- Any "unexplained crying" or "restless heart" sensations
Note: In TCM, women are blood-based; emotions first damage liver blood, then Chong-Ren. Pay attention to the chain: Liver Qi Stagnation → Blood Deficiency → Chong-Ren Disharmony."""
        else:
            return """\n[Emotional Assessment (Male)]
Male emotional issues often present as somatic symptoms. Watch for these proxy indicators:
- Sudden decline in sleep quality
- Noticeable decrease in libido
- Appetite changes (binge eating or loss of appetite)
- Self-reported decline in work efficiency
- Descriptions of social withdrawal
Note: Men are essence-based; emotions first damage liver's dispersing function, then kidneys over time. If 3+ proxy indicators are positive, include an emotional analysis section in the diagnosis report."""


def get_wellness_differentiation(gender: str, stage: str, locale: str = "zh") -> str:
    if not gender or not stage:
        return ""

    if locale == "zh":
        lines = ["\n【调养建议差异化】"]
        lines.append(f"用户：{gender}，{STAGE_LABELS['zh'].get(stage, stage)}")

        if gender == "女":
            lines.append("""
穴位按摩建议：
  疏肝解郁：太冲（疏肝）+ 三阴交（调经养血）+ 膻中（宽胸）

食疗建议：
  偏养血：阿胶、红枣、龙眼、当归炖鸡

运动建议：
  八段锦（动作舒缓，不过度耗气）""")

            if stage == "perimenopausal":
                lines.append("""
围绝经期专项建议：
  饮食：增加豆类（含植物雌激素）、减少辛辣
  作息：避免熬夜（阴虚火旺容易夜间加重）
  情志：重点说明情绪与症状的关联，鼓励倾诉
  运动：瑜伽/八段锦，注意骨质疏松风险""")
        else:
            lines.append("""
穴位按摩建议：
  疏肝解郁：太冲（疏肝）+ 期门（肝募）+ 阳陵泉（胆经）

食疗建议：
  偏填精：山药、枸杞、核桃、黑芝麻

运动建议：
  可加强度，推荐慢跑/太极拳""")

    else:
        lines = ["\n[Wellness Differentiation]"]
        lines.append(f"User: {gender}, {STAGE_LABELS['en'].get(stage, stage)}")

        if gender == "女":
            lines.append("""
Acupressure:
  Liver soothing: Taichong (LV-3) + Sanyinjiao (SP-6, regulates menstruation) + Shanzhong (CV-17, opens chest)

Diet therapy:
  Blood-nourishing: Donkey-hide gelatin, red dates, longan, Angelica chicken soup

Exercise:
  Baduanjin (gentle movements, does not over-consume Qi)""")

            if stage == "perimenopausal":
                lines.append("""
Perimenopausal specific:
  Diet: Increase legumes (phytoestrogens), reduce spicy foods
  Sleep: Avoid staying up late (Yin Deficiency Fire worsens at night)
  Emotional: Explain the connection between emotions and symptoms, encourage expression
  Exercise: Yoga/Baduanjin, be aware of osteoporosis risk""")
        else:
            lines.append("""
Acupressure:
  Liver soothing: Taichong (LV-3) + Qimen (LV-14, Liver's front-Mu) + Yanglingquan (GB-34, Gallbladder)

Diet therapy:
  Essence-nourishing: Chinese yam, goji berries, walnuts, black sesame

Exercise:
  Moderate intensity recommended, jogging/Tai Chi""")

    return "\n".join(lines)


def get_safety_mode(session: dict, locale: str = "zh") -> dict:
    en = locale == "en"
    gender = session.get("gender")
    menstrual = session.get("menstrual_data") or {}
    pregnancy = session.get("pregnancy_status")

    result = {"mode": "standard", "warnings": []}

    if not gender:
        return result

    def label(key: str) -> str:
        mode = FEMALE_SAFETY_MODES[key]
        return mode["label_en"] if en else mode["label_zh"]

    if gender == "女":
        if pregnancy in ("pregnant_early", "pregnant_late"):
            result["mode"] = label(pregnancy)
            result["safety_mode"] = pregnancy
            result["warnings"].append(
                "All pregnancy-contraindicated herbs are blocked. Confirm every recommended herb is safe in pregnancy."
                if en else
                "妊娠禁忌药全量屏蔽。请确认所有推荐药材均可安全使用。"
            )
            return result
        if pregnancy == "planning_pregnancy":
            result["mode"] = label("planning_pregnancy")
            result["safety_mode"] = "planning_pregnancy"
            result["warnings"].append(
                "Avoid blood-activating/breaking herbs, strongly cold herbs that damage Yang, and Tripterygium/Woolly cotton root."
                if en else
                "禁活血破血类、禁大寒伤阳类、禁雷公藤、棉花根等。"
            )
            return result
        if pregnancy == "breastfeeding":
            result["mode"] = label("breastfeeding")
            result["safety_mode"] = "breastfeeding"
            result["warnings"].append(
                "Avoid strongly bitter-cold herbs, strong menstrual-moving herbs, and milk-suppressing herbs (e.g., malt)."
                if en else
                "禁大苦大寒类、禁强通经药、禁回乳药（麦芽等）。"
            )
            return result

        menstrual_flow = menstrual.get("flow")
        menstrual_color = menstrual.get("color")

        if menstrual.get("is_menstruating"):
            if menstrual_flow in ("多", "heavy", "崩漏"):
                result["mode"] = label("menstrual_heavy")
                result["safety_mode"] = "menstrual_heavy"
                result["warnings"].append(
                    "Heavy menstrual flow: avoid blood-activating herbs; astringent hemostatics may be used."
                    if en else
                    "经期量多，禁活血化瘀类。可用收涩止血类。"
                )
            elif menstrual_color in ("暗红", "dark red", "有血块", "with clots"):
                result["mode"] = label("menstrual_blood_stasis")
                result["safety_mode"] = "menstrual_blood_stasis"
                result["warnings"].append(
                    "Menstrual blood-stasis pattern: blood-activating herbs are appropriate; avoid astringent hemostatics."
                    if en else
                    "经期血瘀型，宜活血化瘀，禁收涩止血类。"
                )
            else:
                result["mode"] = label("menstrual_normal")
                result["safety_mode"] = "menstrual_normal"
                result["warnings"].append(
                    "Normal menstruation: avoid strongly cold herbs and drastic purgatives."
                    if en else
                    "经期一般情况，禁大寒、禁峻下。"
                )

    if gender == "男":
        if session.get("male_fertility_need", False):
            result["mode"] = "Caution Mode (Male Fertility)" if en else "注意模式（男性生育需求）"
            result["safety_mode"] = "male_fertility"
            result["warnings"].append(
                "Fertility is desired. Long-term use of these herbs may impair reproductive function: Tripterygium wilfordii, Woolly cotton root, and prolonged high-dose heat-clearing herbs."
                if en else
                "有生育需求，以下药材长期使用可能影响生殖功能：雷公藤、棉花根、长期大量清热解毒类。"
            )

    return result


def get_round0_intro(locale: str, gender: str, stage: str = None) -> str:
    stage_label = STAGE_LABELS.get(locale, STAGE_LABELS["zh"]).get(stage, "") if stage else ""

    if locale == "zh":
        if gender == "女":
            base = "我先了解您最主要的不适，同时确认几项会影响用药安全的基本情况（如孕产状态），这样才能给出适合您的建议。"
            if stage == "perimenopausal":
                base += " 您正处于围绝经期，我也会顺带了解一些相关的身体变化。"
            return base
        else:
            base = "我先了解您最主要的不适，同时确认几项基础情况（精力、腰膝、睡眠等），这样才能准确判断您的体质。"
            return base
    else:
        if gender == "女":
            base = "Let me first understand your main concern, along with a few basics that affect medication safety (such as pregnancy status), so I can give you appropriate advice."
            if stage == "perimenopausal":
                base += " Since you are in the perimenopausal stage, I'd also like to understand some related bodily changes."
            return base
        else:
            base = "Let me first understand your main concern, along with a few basics about your energy, back and knees, and sleep, so I can assess your constitution accurately."
            return base