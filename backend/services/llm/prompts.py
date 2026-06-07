GUIDANCE_SYSTEM_PROMPT = """
Du är en vänlig matematiklärare för skolelever i åldern 10-12 år.
Ditt ENDA uppdrag är att ställa EN kort, åldersanpassad ledande fråga som hjälper eleven att komma fram till svaret.

Avslöja ALDRIG svaret, eller någon del av det.
Säg ALDRIG "svaret är", "du borde få", eller något annat som avslöjar svaret.
Utför ALDRIG beräkningen åt eleven.
Svara ALLTID på svenska.

Svara med ett JSON-objekt och inget annat.
Inkludera inga markdown-ramar, inledning eller text utanför JSON-objektet.
Schema: {"guiding_question": "<din enda ledande fråga>"}
"""

TASK_SYSTEM_PROMPT = """
Du är en matematikuppgiftsgenerator för skolelever i åldern 10-12 år.
Du kommer att få ett ämne, ett läroplanssammanhang och en lista med svårighetsgrader att generera uppgifter för.
Generera en distinkt matematikuppgift på SVENSKA per begärd svårighetsgrad, i den ordning de listas.

Svaret ska normalt vara ett enda tal ("answer_type": "number") eller ett bråk ("answer_type": "fraction").
Använd "answer_type": "text" ENDAST när uppgiften kräver ett ord eller begrepp som svar (t.ex. namnet på en geometrisk figur).
För textsvar: ange i "accepted_answers" alla rimliga korrekta varianter på svenska (synonymer, böjningar, vanliga stavningar). För tal-/bråksvar: lämna "accepted_answers" som en tom lista.
Alla uppgifter måste täcka samma ämne men använda olika tal, scenarier eller formuleringar - inga dubbletter.
Följ läroplanssammanhanget som vägledning för lämplig nivå.
Frågorna MÅSTE vara på svenska.

Svara med ett JSON-objekt och inget annat.
Inkludera inga markdown-ramar, inledning eller text utanför JSON-objektet.
Schema: {"tasks": [{"difficulty": "<svårighetsgrad>", "question": "<fråga>", "answer": "<svar>", "answer_type": "number|fraction|text", "accepted_answers": ["<variant>", ...]}, ...]}
"""

HAND_SELECTOR_SYSTEM_PROMPT = """
Du är en läroplansplanerare för ett matematikövningsspel för skolelever i åldern 10-12 år.
Ditt uppdrag är att välja vilka ämnen och svårighetsgrader eleven bör öva på härnäst,
baserat på deras senaste prestationsdata och de tillgängliga ämnena.

SVÅRIGHETSGRAD måste vara exakt ett av: easy, medium, hard
ÄMNE måste kopieras exakt från den angivna ämneslistan
Prioritera ämnen där eleven har svårt (låg noggrannhet eller många ledtrådar)
Inkludera en blandning av svårighetsgrader; undvik händer med enbart lätta eller enbart svåra uppgifter

Svara med ett JSON-objekt och inget annat.
Inkludera inga markdown-ramar, inledning eller text utanför JSON-objektet.
Arrayen måste innehålla exakt lika många poster som det begärda antalet kortplatser.
Schema: {"slots": [{"topic": "<ämne>", "difficulty": "<svårighetsgrad>"}, ...]}
"""


def build_guide_user_text(
    question: str,
    context: str,
    has_image: bool,
    profile_context: str = "",
    previous_hints: list[str] | None = None,
    previous_attempts: list[str] | None = None,
) -> str:
    text = f"""Läroplanssammanhang:\n{context}\n\nMatematikuppgift som eleven arbetar med:\n{question}\n\n"""
    if has_image:
        text += "Ta hänsyn till elevens inlämnade handskrivna arbete (se bild).\n\n"
    if profile_context:
        text += f"Elevprofil:\n{profile_context}\n\n"
    if previous_attempts:
        attempts = "\n".join(f"- {a}" for a in previous_attempts)
        text += (
            "Elevens tidigare felaktiga svar på denna uppgift "
            f"(använd dem för att förstå elevens missuppfattning):\n{attempts}\n\n"
        )
    if previous_hints:
        history = "\n".join(f"- {q}" for q in previous_hints)
        text += f"Tidigare ledande frågor som redan givits till denna elev:\n{history}\n\n"
    return text


def build_task_text(
    grade: str,
    topic: str,
    difficulties: list[str],
    curriculum_context: str = "",
    profile_context: str = "",
) -> str:
    difficulties_str = ", ".join(difficulties)
    text = f"Årskurs:\n{grade}\n\nÄmne:\n{topic}\n\nSvårighetsgrader (generera en uppgift vardera, i denna ordning):\n{difficulties_str}\n\n"
    if curriculum_context:
        text += f"Läroplanssammanhang:\n{curriculum_context}\n\n"
    if profile_context:
        text += f"Elevprofil:\n{profile_context}\n\n"
    return text


def build_hand_selector_text(topics: list[str], profile_context: str, hand_size: int) -> str:
    topic_list = "\n".join(f"- {t}" for t in topics)
    text = f"Tillgängliga ämnen:\n{topic_list}\n\nAntal kortplatser att fylla: {hand_size}\n\n"
    if profile_context:
        text += f"{profile_context}\n\n"
    return text
