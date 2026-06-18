from __future__ import annotations

from dataclasses import dataclass

from .schemas import StrategyName


ADVANCED_SYSTEM_PROMPT = """You are a senior executive communication specialist and business email writing assistant.
Your job is to convert structured user input into a polished professional English email.
Rules:
1. Include every user-provided key fact accurately and naturally.
2. Do not invent unsupported facts, dates, promises, attachments, names, or outcomes.
3. Match the requested tone exactly while staying professional.
4. Use clear email structure: subject, greeting, body, call-to-action when useful, and sign-off.
5. Keep the writing concise, specific, and easy to understand.
6. If the provided facts are incomplete, write naturally without pretending to know missing details.
7. Output only valid JSON that matches the requested schema.
8. Do not reveal hidden reasoning or chain-of-thought.
Before finalizing, silently check:
- Are all key facts included?
- Is the tone correct?
- Is the email professional and complete?
- Is there any unsupported information? If yes, remove it."""


FEW_SHOT_EXAMPLES = """Example 1
Input:
Intent: Follow up after a sales meeting
Key Facts:
- Meeting was held yesterday
- Discussed CRM migration
- Client requested pricing options
- Send proposal by Thursday
Tone: Formal
Output JSON:
{
"subject": "Follow-Up on CRM Migration Discussion",
"email": "Dear [Recipient],\\n\\nThank you for taking the time to meet with us yesterday to discuss the CRM migration. I appreciate the opportunity to better understand your requirements and the pricing options you would like us to include.\\n\\nAs discussed, we will prepare and share the proposal by Thursday, including the relevant pricing options for your review. Please let me know if there are any additional requirements you would like us to consider before then.\\n\\nBest regards,\\n[Your Name]",
"included_facts": ["Meeting was held yesterday", "Discussed CRM migration", "Client requested pricing options", "Send proposal by Thursday"],
"missing_facts": [],
"tone_used": "Formal",
"notes": "All facts were included in a formal follow-up structure."
}

Example 2
Input:
Intent: Apologize for a delayed delivery
Key Facts:
- Delivery is delayed by two days
- QA found an issue in the final build
- Team is fixing the issue now
- New delivery date is Wednesday
Tone: Empathetic
Output JSON:
{
"subject": "Update on Delivery Timeline",
"email": "Hi [Recipient],\\n\\nI sincerely apologize for the delay in the delivery timeline. During final QA, our team found an issue in the build that needs to be fixed before we send it over.\\n\\nThe team is working on the issue now, and we expect to deliver the corrected version by Wednesday. I understand this may cause inconvenience, and I appreciate your patience while we make sure the final delivery meets the right quality standard.\\n\\nBest regards,\\n[Your Name]",
"included_facts": ["Delivery is delayed by two days", "QA found an issue in the final build", "Team is fixing the issue now", "New delivery date is Wednesday"],
"missing_facts": [],
"tone_used": "Empathetic",
"notes": "The email acknowledges inconvenience, explains the reason, and provides a clear new date."
}"""


ADVANCED_USER_TEMPLATE = """Write a professional English email using the following inputs.

Intent:
{intent}

Key Facts that must be included:
{key_facts}

Requested Tone:
{tone}

Return only valid JSON in this exact format:
{{
"subject": "A clear subject line",
"email": "The full email body with greeting and sign-off",
"included_facts": ["List the user facts that were included"],
"missing_facts": ["List any user facts that could not be included; otherwise empty"],
"tone_used": "The tone actually used",
"notes": "Very brief note on how the email satisfied the request"
}}"""


BASELINE_SYSTEM_PROMPT = """You are a professional English email writing assistant. Write only in English."""


BASELINE_USER_TEMPLATE = """Write a professional English email based on the following information.
Intent: {intent}
Key Facts: {key_facts}
Tone: {tone}
Include a subject line and email body."""


REPAIR_SYSTEM_PROMPT = """You are improving a generated professional English email. Return only valid JSON using the requested schema. Do not reveal hidden reasoning."""


REPAIR_USER_TEMPLATE = """Original Input:
Intent: {intent}
Key Facts: {key_facts}
Tone: {tone}

Previous Generated Email:
Subject: {subject}

{generated_email}

Problems Found:
{failure_reasons}

Rewrite the email so that:
1. Every missing fact is included accurately.
2. The requested tone is improved.
3. The structure remains professional.
4. Unsupported or invented details are removed.
5. The result is concise and polished.

Return only valid JSON using this schema:
{{
"subject": "A clear subject line",
"email": "The full email body with greeting and sign-off",
"included_facts": ["List the user facts that were included"],
"missing_facts": ["List any user facts that could not be included; otherwise empty"],
"tone_used": "The tone actually used",
"notes": "Very brief note on how the email satisfied the request"
}}"""


@dataclass(frozen=True)
class PromptBundle:
    messages: list[dict[str, str]]
    prompt_version: str


def format_key_facts(key_facts: list[str]) -> str:
    return "\n".join(f"- {fact}" for fact in key_facts)


def build_generation_messages(
    *,
    intent: str,
    key_facts: list[str],
    tone: str,
    strategy: StrategyName,
    prompt_version: str,
) -> PromptBundle:
    if strategy == StrategyName.simple:
        return PromptBundle(
            messages=[
                {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": BASELINE_USER_TEMPLATE.format(
                        intent=intent,
                        key_facts="; ".join(key_facts),
                        tone=tone,
                    ),
                },
            ],
            prompt_version=f"{prompt_version}:simple-baseline",
        )

    advanced_user = ADVANCED_USER_TEMPLATE.format(
        intent=intent,
        key_facts=format_key_facts(key_facts),
        tone=tone,
    )
    return PromptBundle(
        messages=[
            {"role": "system", "content": ADVANCED_SYSTEM_PROMPT},
            {"role": "user", "content": FEW_SHOT_EXAMPLES},
            {"role": "user", "content": advanced_user},
        ],
        prompt_version=f"{prompt_version}:advanced-production",
    )


def build_repair_messages(
    *,
    intent: str,
    key_facts: list[str],
    tone: str,
    subject: str,
    generated_email: str,
    failure_reasons: list[str],
    prompt_version: str,
) -> PromptBundle:
    content = REPAIR_USER_TEMPLATE.format(
        intent=intent,
        key_facts=format_key_facts(key_facts),
        tone=tone,
        subject=subject,
        generated_email=generated_email,
        failure_reasons="\n".join(f"- {reason}" for reason in failure_reasons),
    )
    return PromptBundle(
        messages=[
            {"role": "system", "content": REPAIR_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        prompt_version=f"{prompt_version}:repair",
    )

