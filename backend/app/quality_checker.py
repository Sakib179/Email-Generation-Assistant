from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .config import Settings
from .llm_gateway import GroqGateway, LLMGatewayError
from .schemas import GeneratedEmailDraft, JudgeScores, QualityScores


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "client",
    "customer",
    "candidate",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "new",
    "the",
    "to",
    "us",
    "was",
    "we",
    "will",
    "with",
    "you",
    "your",
}


JUDGE_SYSTEM_PROMPT = """You are an impartial evaluator for a professional English email generation assistant.
Return only valid JSON. Do not include hidden reasoning or chain-of-thought."""


JUDGE_USER_TEMPLATE = """Evaluate the generated email against the original user input and the human reference email.

Original Intent:
{intent}

Required Key Facts:
{key_facts}

Requested Tone:
{tone}

Human Reference Email:
{human_reference_email}

Generated Email:
Subject: {subject}

{generated_email}

Score the generated email using these metrics:
1. Fact Recall and Integration Score: 0-10
2. Tone and Audience Fit Score: 0-10
3. Professional Email Quality Score: 0-10

Important judging rules:
- Judge primarily against the original intent, required facts, and requested tone.
- Use the human reference email as a style and quality benchmark, not an exact wording requirement.
- Do not penalize placeholder names such as [Recipient] or [Your Name] when the original input did not provide real names.
- Do not require personal details, company names, attachments, or facts that were not provided in the original input.
- If a required fact is expressed as a natural paraphrase, count it as included.

Return only valid JSON:
{{
"fact_recall_integration_score": 0,
"tone_audience_fit_score": 0,
"professional_email_quality_score": 0,
"overall_score": 0,
"missing_facts": [],
"hallucination_flag": false,
"reason": "Brief explanation"
}}"""


@dataclass(frozen=True)
class AutomatedChecks:
    fact_presence_score: float
    structure_score: float
    tone_score: float
    missing_facts: list[str] = field(default_factory=list)
    included_facts: list[str] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QualityResult:
    scores: QualityScores
    missing_facts: list[str]
    included_facts: list[str]
    hallucination_flag: bool = False
    judge_reason: str = ""
    failure_reasons: list[str] = field(default_factory=list)


class QualityChecker:
    def __init__(self, settings: Settings, gateway: GroqGateway | None = None):
        self.settings = settings
        self.gateway = gateway

    async def evaluate(
        self,
        *,
        intent: str,
        key_facts: list[str],
        tone: str,
        draft: GeneratedEmailDraft,
        human_reference_email: str | None = None,
        use_llm_judge: bool = True,
    ) -> QualityResult:
        automated = self.run_automated_checks(key_facts=key_facts, tone=tone, draft=draft)
        judge = None
        if use_llm_judge and self.gateway and self.settings.has_groq_key:
            try:
                judge = await self._run_llm_judge(
                    intent=intent,
                    key_facts=key_facts,
                    tone=tone,
                    draft=draft,
                    human_reference_email=human_reference_email,
                )
            except (LLMGatewayError, ValueError) as exc:
                judge = None
                public_message = getattr(exc, "public_message", str(exc))
                automated = self._append_failure(automated, f"LLM judge unavailable: {public_message}")

        scores = self._combine_scores(automated, judge)
        missing = sorted(set(automated.missing_facts))
        failure_reasons = list(automated.failure_reasons)
        if scores.fact_recall_integration < self.settings.fact_threshold:
            failure_reasons.append(
                f"Fact Recall and Integration Score is below threshold: {scores.fact_recall_integration:.1f}."
            )
        if scores.tone_audience_fit < self.settings.tone_threshold:
            failure_reasons.append(f"Tone and Audience Fit Score is below threshold: {scores.tone_audience_fit:.1f}.")
        if scores.professional_email_quality < self.settings.quality_threshold:
            failure_reasons.append(
                f"Professional Email Quality Score is below threshold: {scores.professional_email_quality:.1f}."
            )
        if scores.overall < self.settings.overall_threshold:
            failure_reasons.append(f"Overall score is below threshold: {scores.overall:.1f}.")
        for fact in missing:
            if fact not in failure_reasons:
                failure_reasons.append(f"Missing or weakly integrated fact: {fact}")

        return QualityResult(
            scores=scores,
            missing_facts=missing,
            included_facts=automated.included_facts,
            hallucination_flag=bool(judge.hallucination_flag if judge else False),
            judge_reason=(judge.reason if judge else "Deterministic checks only."),
            failure_reasons=failure_reasons,
        )

    def run_automated_checks(
        self,
        *,
        key_facts: list[str],
        tone: str,
        draft: GeneratedEmailDraft,
    ) -> AutomatedChecks:
        email_text = f"{draft.subject}\n{draft.email}"
        missing_facts: list[str] = []
        included_facts: list[str] = []
        for fact in key_facts:
            if self._fact_is_present(fact, email_text):
                included_facts.append(fact)
            else:
                missing_facts.append(fact)
        fact_score = (len(included_facts) / max(len(key_facts), 1)) * 10

        structure_points = [
            bool(draft.subject and 4 <= len(draft.subject) <= 160),
            self._has_greeting(draft.email),
            len(self._paragraphs(draft.email)) >= 2,
            self._has_call_to_action(draft.email),
            self._has_signoff(draft.email),
            40 <= len(draft.email.split()) <= 260,
        ]
        structure_score = (sum(structure_points) / len(structure_points)) * 10
        tone_score = self._tone_heuristic(tone, draft.email)

        failure_reasons: list[str] = []
        if missing_facts:
            failure_reasons.extend(f"Missing required fact: {fact}" for fact in missing_facts)
        if not self._has_greeting(draft.email):
            failure_reasons.append("Email is missing a clear greeting.")
        if not self._has_signoff(draft.email):
            failure_reasons.append("Email is missing a professional sign-off.")
        if not draft.subject:
            failure_reasons.append("Subject line is missing.")
        if len(draft.email.split()) > 260:
            failure_reasons.append("Email is too long for the default concise requirement.")

        return AutomatedChecks(
            fact_presence_score=round(fact_score, 2),
            structure_score=round(structure_score, 2),
            tone_score=round(tone_score, 2),
            missing_facts=missing_facts,
            included_facts=included_facts,
            failure_reasons=failure_reasons,
        )

    async def _run_llm_judge(
        self,
        *,
        intent: str,
        key_facts: list[str],
        tone: str,
        draft: GeneratedEmailDraft,
        human_reference_email: str | None,
    ) -> JudgeScores:
        assert self.gateway is not None
        result = await self.gateway.chat_completion(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": JUDGE_USER_TEMPLATE.format(
                        intent=intent,
                        key_facts="\n".join(f"- {fact}" for fact in key_facts),
                        tone=tone,
                        human_reference_email=human_reference_email or "Not provided.",
                        subject=draft.subject,
                        generated_email=draft.email,
                    ),
                },
            ],
            model_override=self.settings.judge_model,
            temperature=self.settings.judge_temperature,
            max_tokens=self.settings.max_judge_tokens,
            use_fallback=True,
        )
        return JudgeScores.model_validate(_normalize_judge_payload(_loads_json_object(result.content)))

    def _combine_scores(self, automated: AutomatedChecks, judge: JudgeScores | None) -> QualityScores:
        if judge:
            fact = (0.70 * automated.fact_presence_score) + (0.30 * judge.fact_recall_integration_score)
            tone = (0.40 * automated.tone_score) + (0.60 * judge.tone_audience_fit_score)
            quality = (0.40 * automated.structure_score) + (0.60 * judge.professional_email_quality_score)
        else:
            fact = automated.fact_presence_score
            tone = automated.tone_score
            quality = automated.structure_score
        overall = (fact + tone + quality) / 3
        return QualityScores(
            fact_recall_integration=round(min(max(fact, 0), 10), 2),
            tone_audience_fit=round(min(max(tone, 0), 10), 2),
            professional_email_quality=round(min(max(quality, 0), 10), 2),
            overall=round(min(max(overall, 0), 10), 2),
        )

    @staticmethod
    def _append_failure(checks: AutomatedChecks, reason: str) -> AutomatedChecks:
        return AutomatedChecks(
            fact_presence_score=checks.fact_presence_score,
            structure_score=checks.structure_score,
            tone_score=checks.tone_score,
            missing_facts=checks.missing_facts,
            included_facts=checks.included_facts,
            failure_reasons=[*checks.failure_reasons, reason],
        )

    @staticmethod
    def _filter_judge_missing_facts(key_facts: list[str], judge_missing: list[str]) -> list[str]:
        filtered: list[str] = []
        for missing in judge_missing:
            missing_tokens = set(_important_tokens(missing))
            if not missing_tokens:
                continue
            best_fact = None
            best_ratio = 0.0
            for fact in key_facts:
                fact_tokens = set(_important_tokens(fact))
                if not fact_tokens:
                    continue
                overlap = len(missing_tokens & fact_tokens)
                ratio = overlap / max(min(len(missing_tokens), len(fact_tokens)), 1)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_fact = fact
            if best_fact and best_ratio >= 0.5:
                filtered.append(best_fact)
        return filtered

    @staticmethod
    def _fact_is_present(fact: str, email_text: str) -> bool:
        fact_tokens = _important_tokens(fact)
        if not fact_tokens:
            return True
        text = _normalize(email_text)
        text_tokens = set(_tokenize(text))
        expanded_text_tokens = _expand_tokens(text_tokens)
        overlap = sum(1 for token in fact_tokens if _token_matches(token, expanded_text_tokens))
        overlap_ratio = overlap / len(fact_tokens)

        fact_numbers = re.findall(r"[$#]?[A-Za-z]*-?\d[\w,.:-]*", fact.lower())
        numbers_present = all(number.strip(".,").lower() in text for number in fact_numbers)
        if fact_numbers and numbers_present and overlap_ratio >= 0.35:
            return True
        return overlap_ratio >= 0.55

    @staticmethod
    def _has_greeting(email: str) -> bool:
        first_line = email.strip().splitlines()[0].lower() if email.strip() else ""
        return first_line.startswith(("dear ", "hi ", "hello ", "good morning", "good afternoon"))

    @staticmethod
    def _has_signoff(email: str) -> bool:
        lower = email.lower()
        return any(
            phrase in lower
            for phrase in ["best regards", "kind regards", "sincerely", "thank you", "thanks,", "regards,"]
        )

    @staticmethod
    def _has_call_to_action(email: str) -> bool:
        lower = email.lower()
        return any(
            phrase in lower
            for phrase in [
                "please let me know",
                "could you",
                "would you",
                "please confirm",
                "please share",
                "i would appreciate",
                "next step",
                "by ",
                "availability",
                "approval",
                "update",
            ]
        )

    @staticmethod
    def _paragraphs(email: str) -> list[str]:
        return [p.strip() for p in re.split(r"\n\s*\n", email.strip()) if p.strip()]

    @staticmethod
    def _tone_heuristic(tone: str, email: str) -> float:
        lower_tone = tone.lower()
        lower_email = email.lower()
        score = 8.0
        if "urgent" in lower_tone:
            score += 1.0 if any(word in lower_email for word in ["urgent", "deadline", "by noon", "as soon"]) else -1.0
            score -= 1.0 if any(word in lower_email for word in ["immediately!", "failure", "unacceptable"]) else 0
        if "empathetic" in lower_tone or "calm" in lower_tone:
            score += 1.0 if any(word in lower_email for word in ["apologize", "understand", "appreciate", "sorry"]) else -1.0
        if "firm" in lower_tone:
            score += 0.8 if any(word in lower_email for word in ["please confirm", "payment", "due", "appreciate"]) else -0.8
        if "executive" in lower_tone or "concise" in lower_tone:
            score += 0.8 if len(email.split()) <= 150 else -1.0
        if "friendly" in lower_tone or "casual" in lower_tone:
            score += 0.5 if email.strip().lower().startswith(("hi ", "hello ")) else -0.3
        return min(max(score, 0), 10)


def _loads_json_object(content: str) -> dict[str, Any]:
    content = content.strip()
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(content[start : end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("No valid JSON object found in LLM response")


def _normalize_judge_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    score_fields = [
        "fact_recall_integration_score",
        "tone_audience_fit_score",
        "professional_email_quality_score",
    ]
    for field_name in score_fields:
        normalized[field_name] = _coerce_score(normalized.get(field_name, 0))
    if "overall_score" in normalized:
        normalized["overall_score"] = _coerce_score(normalized["overall_score"])
    else:
        normalized["overall_score"] = round(sum(normalized[field] for field in score_fields) / 3, 2)
    if not isinstance(normalized.get("missing_facts"), list):
        normalized["missing_facts"] = []
    normalized["missing_facts"] = [str(item) for item in normalized["missing_facts"]]
    normalized["hallucination_flag"] = bool(normalized.get("hallucination_flag", False))
    normalized["reason"] = str(normalized.get("reason") or "Judge returned normalized scores.")
    return normalized


def _coerce_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return round(min(max(score, 0.0), 10.0), 2)


def _normalize(value: str) -> str:
    value = value.replace("\u2010", "-").replace("\u2011", "-").replace("\u2012", "-").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", value.lower())


def _tokenize(value: str) -> list[str]:
    value = _normalize(value)
    tokens = []
    for token in re.findall(r"[a-z0-9$#][a-z0-9$#,.:-]*", value):
        clean = token.strip(".,:;")
        if clean:
            tokens.append(clean)
            if "-" in clean:
                tokens.extend(part for part in clean.split("-") if part)
    return tokens


def _important_tokens(value: str) -> list[str]:
    tokens = []
    for token in _tokenize(value):
        clean = token.lower()
        if clean and clean not in STOPWORDS and len(clean) > 1:
            tokens.append(clean)
    return tokens


ALIASES: dict[str, set[str]] = {
    "apologize": {"apologize", "apology", "apologies", "sorry", "apologise"},
    "apology": {"apologize", "apology", "apologies", "sorry", "apologise"},
    "ask": {"ask", "asked", "request", "requested", "inquire", "inquired", "confirm", "share", "provide", "need", "seek", "seeking", "advise"},
    "asked": {"ask", "asked", "request", "requested", "inquire", "inquired", "confirm", "share", "provide", "need", "seek", "seeking", "advise"},
    "availability": {"availability", "available", "convenient", "suits"},
    "attach": {"attach", "attached", "attachment", "enclosed"},
    "attached": {"attach", "attached", "attachment", "enclosed"},
    "complete": {"complete", "completed", "finished", "finalized", "done"},
    "completed": {"complete", "completed", "finished", "finalized", "done"},
    "deadline": {"deadline", "due", "needed", "required", "by"},
    "depends": {"depends", "dependent", "requires", "required", "cannot", "without", "proceed"},
    "dependent": {"depends", "dependent", "requires", "required", "cannot", "without", "proceed"},
    "delivery": {"delivery", "deliver", "delivered"},
    "discussed": {"discussed", "discussion", "discuss"},
    "implementation": {"implementation", "implement", "deployment", "rollout"},
    "link": {"link", "url", "here"},
    "payment": {"payment", "pay", "paid"},
    "proposal": {"proposal", "proposed"},
    "reported": {"reported", "received", "raised", "shared", "notified"},
    "requested": {"ask", "asked", "request", "requested", "inquire", "inquired", "confirm", "share", "provide", "need", "seek", "seeking", "advise"},
    "share": {"share", "shared", "send", "provide", "view", "see"},
    "suggest": {"suggest", "suggested", "propose", "proposed", "set", "schedule", "arrange"},
    "timeline": {"timeline", "schedule", "roadmap"},
}


def _expand_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        expanded.update(_token_variants(token))
    return expanded


def _token_matches(token: str, expanded_text_tokens: set[str]) -> bool:
    return bool(_token_variants(token) & expanded_text_tokens)


def _token_variants(token: str) -> set[str]:
    variants = {token}
    if token in ALIASES:
        variants.update(ALIASES[token])
    if token.endswith("ed") and len(token) > 4:
        variants.add(token[:-2])
    if token.endswith("ing") and len(token) > 5:
        variants.add(token[:-3])
    if token.endswith("s") and len(token) > 3:
        variants.add(token[:-1])
    return variants
