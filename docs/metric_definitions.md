# Custom Metric Definitions

The assistant implements exactly three custom metrics.

## Metric 1: Fact Recall and Integration Score

Scale: 0-10

This metric checks whether every required key fact appears accurately and naturally in the generated email. The implementation combines deterministic keyword and number matching with LLM-as-a-judge scoring when a Groq key is available.

Formula:

```text
score = 0.70 * fact_presence_score + 0.30 * llm_natural_integration_score
```

The system penalizes missing facts, distorted facts, unsupported additions, and awkward fact placement.

## Metric 2: Tone and Audience Fit Score

Scale: 0-10

This metric evaluates whether the email matches the requested tone while staying professional and appropriate for the audience. The LLM judge rates formal, casual, urgent, empathetic, persuasive, polite but firm, concise executive, and friendly professional styles. A deterministic tone heuristic stabilizes the score for clear tone markers.

Formula:

```text
score = 0.40 * deterministic_tone_alignment + 0.60 * llm_tone_judge_score
```

## Metric 3: Professional Email Quality Score

Scale: 0-10

This metric checks the email as a professional communication artifact: subject line, greeting, clear body, call-to-action when useful, closing, sign-off, conciseness, grammar, and fluency.

Formula:

```text
score = 0.40 * structure_score + 0.60 * llm_professional_quality_score
```

The deterministic structure score includes subject length, greeting, paragraph count, call-to-action signal, sign-off, and default length boundaries.
