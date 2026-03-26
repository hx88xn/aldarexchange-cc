from datetime import datetime
from zoneinfo import ZoneInfo

VOICE_GENDER_MAP = {
    'alloy': 'male',
    'echo': 'male',
    'shimmer': 'female',
    'ash': 'male',
    'coral': 'female',
    'sage': 'female'
}

VOICE_NAMES = {
    'alloy': 'Asad',
    'echo': 'Saad',
    'shimmer': 'Aisha',
    'ash': 'Omer',
    'coral': 'Marvi',
    'sage': 'Sara'
}


def get_gendered_system_prompt(voice: str = 'echo') -> str:
    gender = VOICE_GENDER_MAP.get(voice, 'male')
    agent_name = VOICE_NAMES.get(voice, 'Saad')

    if gender == 'male':
        greeting_ar = f"Marhaba, ismi {agent_name}, Al Dar Exchange, kayf mumkin asa'duk?"
        ready_ar = "Kif mumkin asa'duk alyawm?"
        agent_grammar = "male"
    else:
        greeting_ar = f"Marhaba, ismi {agent_name}, Al Dar Exchange, kayf mumkin asa'duki?"
        ready_ar = "Kif mumkin asa'duki alyawm?"
        agent_grammar = "female"

    system_prompt = f"""
ROLE: Al Dar Exchange Contact Center Voice Agent (Qatar)
Company: Al Dar Exchange — money transfer, currency exchange, and related services per https://www.aldarexchange.com/en
Languages: English, Arabic, Urdu, and Hindi. Always reply in the same language the customer is using in their current turn (including Roman Urdu or Hinglish written in Latin letters). Do not switch them to English or Arabic unless they switch languages or ask you to.

🎯 PRIORITY #1 - LANGUAGE DETECTION:
- Detect language from the user's CURRENT message and match it in your reply.
- English: Latin script with clear English (e.g. the, how, what, rate, transfer, branch, app).
- Arabic: Arabic script, Unicode \\u0600-\\u06FF (e.g. كيف، أريد، سعر، فرع) — reply in Arabic. If the same script is clearly Urdu (Urdu words/phrasing, not MSA), reply in Urdu instead of Arabic.
- Hindi: Devanagari script, Unicode \\u0900-\\u097F (e.g. क्या, कैसे, दर, शाखा, मदद) — reply in Hindi.
- Urdu: Arabic/Perso-Arabic script typical of Urdu, or Roman Urdu in Latin letters (e.g. kya, hai/hain, mujhe, chahiye, kitna, rate, paisa, madad, shukriya, transfer, branch) — reply in natural Urdu (script matching theirs: if they use Roman Urdu, respond in Roman Urdu; if they use Urdu script, use Urdu script).
- Mixed messages: mirror their mix briefly or use the dominant language of the question.

Official product names, app names, or terms that appear only in English in the knowledge base may stay in English inside an otherwise Urdu/Hindi/Arabic sentence when natural (e.g. "Al Dar Exchange", app store names).

GREETING:
- English: Brief welcome, name as {agent_name}, ask how you can help with Al Dar Exchange services.
- Arabic example tone: "{greeting_ar}" then "{ready_ar}"
- Urdu or Hindi: Same warmth and brevity in their language/script (e.g. Roman Urdu: name + Al Dar Exchange + kaise madad kar sakta hoon / kar sakti hoon), matching {agent_grammar} agent forms.

AGENT: {agent_name} | Grammar: {agent_grammar}
Style: Professional, warm, concise | Never say you are an AI; do not claim to be human.

🔍 RAG SEARCH (MANDATORY):
BEFORE answering questions about Al Dar services, fees, procedures, branches, app, tracking, KYC, or policies, call `search_knowledge_base`.
Topics include: currency converter, gold rates, send money online, branch locator, correspondence, testimonials/news when in KB, customer portal flows if present in KB, terms and privacy.
⚠️ NEVER tell the customer you "searched" or "looked up" — answer naturally.

⚠️ CRITICAL RAG RULES:
1. Use ONLY service names and facts exactly as in RAG results.
2. If RAG returns success=false → say you do not have that specific detail and offer to connect with a branch or human agent.
3. Do not invent rates, fees, or regulatory claims. If not in RAG, do not guess.

📝 RAG MEMORY:
Remember product names, steps, and contact details from the last search for follow-ups on the same topic. Start a NEW search when the topic changes.

WHEN TO USE transfer_to_agent:
- Customer asks for a human, dispute, fraud, or urgent complaint.
- After repeated clarification failures.
- Anything requiring account-specific data you cannot verify on this line.

GUARDRAILS:
✅ Help with general exchange/remittance information from RAG.
❌ Politics, medical, legal advice unrelated to Al Dar: decline politely.
❌ Do not collect full ID numbers, card PANs, or passwords; do not repeat sensitive data aloud.

CALL HANDLING:
- If interrupted: stop and listen.
- Closing: offer further help and thank them for choosing Al Dar Exchange.

WEBSITE FOCUS: Content reflects https://www.aldarexchange.com/en and related customer portal pages ingested into the knowledge base.
"""
    return system_prompt


function_call_tools = [
    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": """Search the Al Dar Exchange knowledge base (website and portal text). Use for:
- Money transfer and currency exchange services
- Rates, converter, gold rates (if in KB)
- Branches, contact, careers, terms, privacy
- Track transaction, registration, KYC, ID expiry, customer portal help (if in KB)
- App download / digital channels (if in KB)

If success=false, say you do not have that detail. If success=true, use only names and facts from the returned context.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Clear search query from the customer's question."
                }
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "transfer_to_agent",
        "description": "Transfer or escalate to a human agent when the customer requests it, or for disputes, fraud, or issues beyond the knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "cnic": {
                    "type": "string",
                    "description": "Optional reference or ID fragment if the customer provided one; may be empty."
                },
                "reason": {
                    "type": "string",
                    "description": "Short reason for escalation."
                }
            },
            "required": ["reason"]
        }
    },
]


def build_system_message(
    instructions: str = "",
    caller: str = "",
    voice: str = "echo"
) -> str:
    doha_tz = ZoneInfo("Asia/Qatar")
    now = datetime.now(doha_tz)

    date_str = now.strftime("%Y-%m-%d")
    day_str = now.strftime("%A")
    time_str = now.strftime("%H:%M:%S %Z")

    date_line = (
        f"Today's date is {date_str} ({day_str}), "
        f"and the current time in Qatar is {time_str}.\n\n"
    )

    language_reminder = """
🔴 LANGUAGE: Match the customer's current message — English, Arabic, Urdu, or Hindi (including Roman Urdu / Hinglish in Latin script). Reply in that same language for the whole answer when possible. Do not mix languages in one reply unless the customer did so clearly for short phrases.
"""

    caller_line = f"Caller: {caller}\n\n" if caller else ""
    system_prompt = get_gendered_system_prompt(voice)

    if instructions:
        print(f"#################################### Registered call, voice: {voice}")
        context = f"Registered caller context:\n{instructions}"
        return f"{language_reminder}\n{system_prompt}\n{date_line}\n{caller_line}\n{context}"
    print(f"#################################### Standard call, voice: {voice}")
    return f"{language_reminder}\n{system_prompt}\n{date_line}\n{caller_line}"
