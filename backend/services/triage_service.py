import re

EMERGENCY_PATTERNS = [
    r"chest pain", r"difficulty breathing", r"can't breathe", r"cannot breathe",
    r"face droop", r"slurred speech", r"weakness on one side", r"unconscious", r"seizure",
    r"severe bleeding", r"suicid", r"stiff neck", r"confusion", r"confused",
    r"faint(?:ed|ing)?", r"severe headache with fever", r"sudden severe headache",
    r"sudden severe headache", r"thunderclap headache", r"blue lips", r"severe allergic reaction",
    r"one sided weakness", r"one-sided weakness", r"drooping face", r"difficulty speaking",
    r"सांस लेने में दिक्कत", r"सांस नहीं आ रही", r"सीने में दर्द", r"अचानक बहुत तेज सिरदर्द",
    r"बेहोश", r"चेहरा टेढ़ा", r"बोलने में दिक्कत", r"एक तरफ कमजोरी", r"गर्दन अकड़"
]
PROMPT_PATTERNS = [r"very high blood pressure", r"very low blood pressure", r"high blood sugar", r"significant swelling", r"new severe cramps", r"very high fever", r"persistent fever", r"blurred vision", r"high blood pressure", r"बहुत तेज बुखार", r"धुंधला दिखना"]
SYMPTOM_PATTERNS = [
    r"\bfever\b", r"headache", r"\bmigraine\b", r"cough", r"cold", r"weakness", r"stomach pain", r"abdominal pain",
    r"vomit(?:ing)?", r"\bulti\b", r"नौ?मिया|मतली|उल्टी", r"nausea", r"diarrh(?:ea|e?a)", r"\bdast\b|दस्त", r"sore throat", r"गले में दर्द", r"dizz(?:y|iness)",
    r"rash", r"skin problem", r"body aches?", r"chills", r"pain", r"breath(?:ing)? difficulty",
    r"सिरदर्द|सिर में दर्द|सर दर्द|सिर दर्द", r"\b(?:sir|sar)\s+dard\b", r"\bbukhar\b|बुखार", r"\bkhansi\b|खांसी|खाँसी",
    r"\bpet\s+dard\b|पेट दर्द|पेट में दर्द", r"\bkamzori\b|कमजोरी", r"\bsardi\b|सर्दी", r"\bneend\b|नींद"
]
VAGUE_PATTERNS = [r"feeling unwell", r"feel unwell", r"not feeling well", r"feel(?:ing)? sick", r"feel(?:ing)? bad", r"\btabiyat\b", r"तबीयत", r"अस्वस्थ"]
TEMPERATURE_PATTERNS = [r"\b\d{2}(?:\.\d)?\s*(?:°\s*)?(?:c|celsius|f|fahrenheit)\b", r"temperature.{0,20}\b\d{2}", r"temp.{0,12}\b\d{2}", r"\b(?:3[5-9]|4[0-2])(?:\.\d)?\b", r"\b10[0-9]\s*°?\s*f\b"]
KNOWN_UNKNOWN_PATTERNS = [r"don't know", r"do not know", r"not sure", r"haven't checked", r"have not checked", r"can't check"]
WARNING_SYMPTOMS = [r"stiff neck", r"confusion", r"confused", r"difficulty breathing", r"can't breathe", r"severe headache", r"faint(?:ed|ing)?"]
NEGATED_SYMPTOM = re.compile(r"\b(?:no|not|without|den(?:y|ies|ied)|nahi|nahin)\b(?:\W+\w+){0,3}\W*$|(?:नहीं|नही)\s*$")

CONCERN_PATTERNS = {
    "headache": [r"headache", r"migraine", r"सिरदर्द|सिर में दर्द|सर दर्द|सिर दर्द", r"\b(?:sir|sar)\s+dard\b"],
    "fever": [r"\bfever\b", r"\bbukhar\b|बुखार"],
    "cough": [r"\bcough\b|\bcold\b|\bkhansi\b|\bsardi\b|खांसी|खाँसी|सर्दी"],
    "throat": [r"sore throat|throat pain|गले में दर्द|गला दर्द"],
    "stomach": [r"stomach pain|abdominal pain|\bpet dard\b|पेट दर्द|पेट में दर्द"],
    "nausea": [r"nausea|\bulti\b|मतली|उल्टी|vomit(?:ing)?"],
    "diarrhea": [r"diarrh(?:ea|e?a)|\bdast\b|दस्त"],
    "rash": [r"rash|skin problem|\bdaane\b|दाने|चकत्ते"],
    "sleep": [r"sleep problem|can't sleep|cannot sleep|\bneend\b|नींद"],
    "weakness": [r"weakness|\bkamzori\b|कमजोरी|fatigue"],
}


def _has_reported_symptom(patterns, text):
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            nearby_context = text[max(0, match.start() - 32):match.start()]
            if not NEGATED_SYMPTOM.search(nearby_context):
                return True
    return False


def assess_symptoms(text):
    cleaned = " ".join(text.lower().split())
    if _has_reported_symptom(EMERGENCY_PATTERNS, cleaned):
        return {"stage": 3, "label": "Emergency warning", "response": "Potential emergency symptoms were reported. Call 112 in India or your local emergency number now, and seek immediate emergency medical care. Do not wait for an online consultation. This is preliminary guidance, not a diagnosis."}
    if _has_reported_symptom(PROMPT_PATTERNS, cleaned):
        return {"stage": 2, "label": "Prompt medical assessment", "response": "Please arrange prompt assessment by a qualified healthcare professional. Seek emergency care immediately if symptoms become severe or you develop chest pain, breathing difficulty, fainting, or confusion. Do not change medication based on this chat."}
    return {"stage": 1, "label": "General health concern", "response": "I can offer general health information, not a diagnosis. Tell me when this started and whether it is getting worse. Rest, fluids, and monitoring may be reasonable for mild symptoms; contact a clinician if it persists, worsens, or concerns you."}


def _has_any(patterns, text):
    return _has_reported_symptom(patterns, text)


def _detect_language(text, preference):
    if preference == "hi" or re.search(r"[\u0900-\u097f]", text):
        return "hi"
    if re.search(r"\b(?:sir dard|sar dard|bukhar|khansi|pet dard|kamzori|tabiyat|ulti|dast|sardi|neend)\b", text.lower()):
        return "hi"
    return "en"


def _answered_no_or_unknown(text):
    return bool(re.search(r"\b(?:no|none|not|without|nothing|negative|nahi|nahin|don't|do not|not sure|unknown)\b|नहीं|नही|नहीं पता", text.lower()))


def _flow_questions(concern, patient_text, message, assistant_text):
    asked_location = "where is the pain" in assistant_text or "where does it hurt" in assistant_text
    asked_associated = any(marker in assistant_text for marker in ("blurred vision", "breathing difficulty", "stiff neck", "trouble breathing"))
    asked_second = any(marker in assistant_text for marker in ("suddenly or gradually", "dry or bringing", "how long", "how severe"))
    has_duration = bool(re.search(r"\b(?:today|yesterday|\d+|one|two|three|four|five|several)\s*(?:days?|weeks?|hours?)\b|\bsince\s+\w+|सुबह से|कल से|दिन से|हफ्ते से", patient_text))
    has_severity = _has_any([r"\b(?:mild|moderate|severe|worsening|worse|improving|better|unchanged|stable)\b", r"हल्का|तेज|गंभीर|बढ़ रहा|कम हो रहा|बेहतर"], patient_text)
    answered_flags = _has_any(WARNING_SYMPTOMS + [r"blurred vision", r"vomiting", r"fever", r"blood in stool"], patient_text) or _answered_no_or_unknown(message)

    if concern == "fever":
        has_temperature = any(re.search(pattern, patient_text) for pattern in TEMPERATURE_PATTERNS)
        unknown_temperature = any(re.search(pattern, patient_text) for pattern in KNOWN_UNKNOWN_PATTERNS)
        asked_temperature = "temperature" in assistant_text or "temp" in assistant_text
        asked_fever_warnings = "stiff neck" in assistant_text or "confusion" in assistant_text or "breathing difficulty" in assistant_text
        answered_fever_warnings = _has_any([r"stiff neck", r"confusion", r"difficulty breathing", r"severe headache"], patient_text) or _answered_no_or_unknown(message)
        if not has_temperature and not unknown_temperature and not asked_temperature:
            return "Do you know your temperature? Are you having a stiff neck, confusion, breathing difficulty, or a severe headache?"
        if not asked_fever_warnings and not answered_fever_warnings:
            return "Do you have a stiff neck, confusion, breathing difficulty, or severe headache? Are the symptoms getting better or worse?"

    if concern == "headache":
        has_location = _has_any([r"forehead", r"one side", r"both sides", r"back of (?:the )?head", r"everywhere", r"all over", r"temples?", r"आगे", r"एक तरफ", r"दोनों तरफ", r"सिर के पीछे"], patient_text)
        if not asked_location and not has_location:
            return "Where is the pain — forehead, one side, back of the head, or everywhere?" + (" Do you have fever, vomiting, blurred vision, dizziness, or neck stiffness?" if not asked_associated and not answered_flags else "")
        if not asked_associated and not answered_flags:
            return "Do you also have fever, vomiting, blurred vision, dizziness, or neck stiffness?"
        onset_known = _has_any([r"sudden", r"gradual", r"slowly", r"quickly", r"came on", r"अचानक", r"धीरे"], patient_text)
        hydration_known = _has_any([r"water", r"hydrated", r"drank", r"sleep", r"rested", r"पानी", r"नींद"], patient_text) or _answered_no_or_unknown(message)
        if not asked_second and (not onset_known or not hydration_known):
            return "Did the headache start suddenly or gradually? Have you had enough water and sleep today?"
        return None

    flows = {
        "fever": ("Do you know your temperature? Are you experiencing breathing difficulty, confusion, a stiff neck, or a severe headache?", "How long have you had the fever, and is it improving or getting worse?", "Rest, drink fluids, and monitor how you feel. Contact a qualified healthcare professional if the fever is high, persists, worsens, or you have other concerning symptoms."),
        "cough": ("Are you having any breathing difficulty, chest pain, or high fever? Is the cough dry or are you bringing up mucus?", "How long have you had the cough, and is it getting better or worse?", "Rest and drink fluids. Seek medical advice if the cough persists or worsens; get urgent help for breathing difficulty, chest pain, confusion, or blue lips."),
        "throat": ("Are you having trouble breathing or swallowing, a high fever, or swelling in your neck?", "When did the sore throat start, and is it improving or worsening?", "Fluids and rest may help mild throat discomfort. Contact a clinician if it persists or worsens; seek urgent care for trouble breathing or swallowing."),
        "stomach": ("Where is the pain, how severe is it, and do you have repeated vomiting, blood, or a high fever?", "When did it start, and is the pain getting worse or spreading?", "For mild discomfort, rest and sip fluids. Seek medical advice if it persists or worsens; urgent care is needed for severe pain, blood, fainting, or repeated vomiting."),
        "nausea": ("Have you vomited, and can you keep fluids down? Do you have severe abdominal pain, blood, or dizziness?", "When did the nausea begin, and is it improving or getting worse?", "Take small sips of fluids if you can. Contact a clinician if it persists; seek urgent help for blood, severe pain, fainting, confusion, or inability to keep fluids down."),
        "diarrhea": ("How often have you had diarrhea, and have you noticed blood, fever, dizziness, or very little urination?", "When did it start, and can you keep fluids down?", "Drink fluids to avoid dehydration. Seek medical advice if it persists or worsens; urgent care is needed for blood, fainting, confusion, or signs of dehydration."),
        "rash": ("Where is the rash, is it spreading, and do you have fever, facial swelling, or trouble breathing?", "When did it start, and has anything changed since it appeared?", "Avoid scratching and monitor changes. Contact a clinician if it spreads, persists, or concerns you; seek emergency help for facial swelling or breathing difficulty."),
        "sleep": ("How long have you had trouble sleeping, and is anything affecting your sleep routine or stress level?", "Is this affecting your daytime activities or wellbeing?", "A regular sleep schedule and a quiet wind-down routine may help. If sleep problems persist or affect daily life, discuss them with a healthcare professional."),
        "weakness": ("Did the weakness start suddenly or affect one side of your body? Do you have fainting, confusion, chest pain, or breathing difficulty?", "When did it begin, and is it getting better or worse?", "Rest and monitor mild weakness, but contact a clinician if it persists or worsens. Sudden one-sided weakness, fainting, confusion, chest pain, or breathing difficulty needs emergency care."),
    }
    first, second, _final = flows.get(concern, ("What symptoms are you experiencing, and when did they start?", "Are they mild, moderate, or severe, and are they improving or getting worse?", "Contact a qualified healthcare professional if your symptoms persist or worsen."))
    if not asked_associated and not answered_flags:
        return first
    if not asked_second and (not has_duration or not has_severity):
        return second
    return None


def respond_conversationally(message, history=None, stage=1, language="en"):
    history = history or []
    patient_messages = [item["content"] for item in history if item.get("sender") == "patient"] + [message]
    assistant_messages = [item["content"].lower() for item in history if item.get("sender") == "assistant"]
    patient_text = " ".join(patient_messages).lower()
    response_language = _detect_language(patient_text, language)
    concerns = [name for name, patterns in CONCERN_PATTERNS.items() if _has_any(patterns, patient_text)]
    if not concerns:
        if _has_any(VAGUE_PATTERNS, patient_text):
            return "मुझे खेद है कि आपकी तबीयत ठीक नहीं है। आपको कौन से लक्षण हो रहे हैं — बुखार, सिरदर्द, खांसी, कमजोरी, पेट दर्द, उल्टी या कुछ और?" if response_language == "hi" else "I'm sorry you're feeling unwell. What symptoms are you experiencing? For example, fever, headache, cough, weakness, stomach pain, vomiting, or something else?"
        return "मैं सामान्य स्वास्थ्य जानकारी दे सकता हूँ। आपको कौन से लक्षण या स्वास्थ्य समस्या हो रही है?" if response_language == "hi" else "I can help with general health information. What symptoms or health concern would you like to discuss?"

    # Prioritize the main concern while retaining every patient turn in the summary.
    concern_order = ("fever", "headache", "cough", "throat", "stomach", "vomiting", "nausea", "diarrhea", "rash", "weakness", "sleep")
    concern = next((name for name in concern_order if name in concerns), concerns[0])
    question = _flow_questions(concern, patient_text, message, " ".join(assistant_messages))
    if question:
        if response_language == "hi":
            if concern == "headache":
                return "दर्द कहाँ है — माथे पर, सिर के एक तरफ, पीछे, या पूरे सिर में? क्या बुखार, उल्टी, धुंधला दिखना, चक्कर या गर्दन में अकड़न भी है?"
            if concern == "fever":
                return "क्या आपको तापमान पता है? क्या सांस लेने में दिक्कत, भ्रम, गर्दन में अकड़न या तेज सिरदर्द है?"
            return "कृपया बताएं लक्षण कब शुरू हुए, कितने गंभीर हैं, और क्या सांस लेने में दिक्कत, तेज दर्द या कोई तेजी से बिगड़ता लक्षण है?"
        return question

    summary = "; ".join(part.strip().rstrip(".; ") for part in patient_messages if part.strip())
    if concern == "headache":
        if response_language == "hi":
            return f"आपने बताया: {summary}। इसके कई संभावित कारण हो सकते हैं, जैसे पानी की कमी, भोजन छूटना, आंखों पर जोर या नींद की कमी; मैं कारण की पुष्टि या निदान नहीं कर सकता। हल्के सिरदर्द में शांत जगह आराम करें, पानी पिएं, भोजन न किया हो तो कुछ खाएं, स्क्रीन से विराम लें और लक्षण देखें। सिरदर्द बना रहे, बढ़े या बार-बार हो तो डॉक्टर से संपर्क करें। अचानक बहुत तेज सिरदर्द, गर्दन में अकड़न, भ्रम, बेहोशी या कमजोरी हो तो तुरंत आपातकालीन सहायता लें।"
        return (f"From what you've shared: {summary}. Common possibilities include dehydration, a missed meal, eye strain, or poor sleep, but I can't confirm the cause or diagnose you. "
                "For a mild headache, rest in a quiet environment, drink water, eat regularly if you missed a meal, take a break from screens, and monitor whether it improves. "
                "Contact a qualified healthcare professional if it persists, worsens, or keeps returning. Seek urgent medical attention for a sudden severe headache, stiff neck, confusion, fainting, weakness, or other rapidly worsening symptoms.")
    final_advice = {
        "fever": "Rest, drink fluids, and monitor how you feel. Contact a qualified healthcare professional if the fever is high, persists, worsens, or you have other concerning symptoms.",
        "cough": "Rest and drink fluids. Seek medical advice if the cough persists or worsens; get urgent help for breathing difficulty, chest pain, confusion, or blue lips.",
        "throat": "Fluids and rest may help mild throat discomfort. Contact a clinician if it persists or worsens; seek urgent care for trouble breathing or swallowing.",
        "stomach": "For mild discomfort, rest and sip fluids. Seek medical advice if it persists or worsens; urgent care is needed for severe pain, blood, fainting, or repeated vomiting.",
        "nausea": "Take small sips of fluids if you can. Contact a clinician if it persists; seek urgent help for blood, severe pain, fainting, confusion, or inability to keep fluids down.",
        "diarrhea": "Drink fluids to avoid dehydration. Seek medical advice if it persists or worsens; urgent care is needed for blood, fainting, confusion, or signs of dehydration.",
        "rash": "Avoid scratching and monitor changes. Contact a clinician if it spreads, persists, or concerns you; seek emergency help for facial swelling or breathing difficulty.",
        "sleep": "A regular sleep schedule and a quiet wind-down routine may help. If sleep problems persist or affect daily life, discuss them with a healthcare professional.",
        "weakness": "Rest and monitor mild weakness, but contact a clinician if it persists or worsens. Sudden one-sided weakness, fainting, confusion, chest pain, or breathing difficulty needs emergency care.",
    }.get(concern, "Contact a qualified healthcare professional if symptoms persist or worsen.")
    if response_language == "hi":
        return f"आपने बताया: {summary}। अलग-अलग कारणों से ऐसे लक्षण हो सकते हैं; मैं कारण की पुष्टि या निदान नहीं कर सकता। {final_advice}"
    return f"From what you've shared: {summary}. Several different causes are possible; I can't determine the cause or provide a diagnosis. {final_advice}"
