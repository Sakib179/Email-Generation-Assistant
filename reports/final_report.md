# Final Report: Email Generation Assistant

## Project Summary
This project builds a production-ready prototype that generates polished professional English emails from Intent, Key Facts, and Tone using Groq-hosted LLMs through a FastAPI backend.

## Recommended Strategy
The recommended production strategy is `advanced` with an overall average of 8.86/10.

## Advanced Prompting Technique
Strategy B uses Role-Playing + Few-Shot Examples + Structured JSON Output + Self-Check/Repair Prompting. This improves quality because the model receives a precise professional role, concrete examples, a parseable output contract, and a repair pass when fact coverage or quality thresholds are not met.

## Exact Strategy B Prompt Template
# Strategy B Production Prompt Template

Prompt version: `email-production-v1.0.0`

## Advanced Generation System Prompt

```text
You are a senior executive communication specialist and business email writing assistant.
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
- Is there any unsupported information? If yes, remove it.
```

## Few-Shot Examples

```text
Example 1
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
"email": "Dear [Recipient],\n\nThank you for taking the time to meet with us yesterday to discuss the CRM migration. I appreciate the opportunity to better understand your requirements and the pricing options you would like us to include.\n\nAs discussed, we will prepare and share the proposal by Thursday, including the relevant pricing options for your review. Please let me know if there are any additional requirements you would like us to consider before then.\n\nBest regards,\n[Your Name]",
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
"email": "Hi [Recipient],\n\nI sincerely apologize for the delay in the delivery timeline. During final QA, our team found an issue in the build that needs to be fixed before we send it over.\n\nThe team is working on the issue now, and we expect to deliver the corrected version by Wednesday. I understand this may cause inconvenience, and I appreciate your patience while we make sure the final delivery meets the right quality standard.\n\nBest regards,\n[Your Name]",
"included_facts": ["Delivery is delayed by two days", "QA found an issue in the final build", "Team is fixing the issue now", "New delivery date is Wednesday"],
"missing_facts": [],
"tone_used": "Empathetic",
"notes": "The email acknowledges inconvenience, explains the reason, and provides a clear new date."
}
```

## Advanced User Prompt Template

```text
Write a professional English email using the following inputs.

Intent:
{{intent}}

Key Facts that must be included:
{{key_facts}}

Requested Tone:
{{tone}}

Return only valid JSON in this exact format:
{
"subject": "A clear subject line",
"email": "The full email body with greeting and sign-off",
"included_facts": ["List the user facts that were included"],
"missing_facts": ["List any user facts that could not be included; otherwise empty"],
"tone_used": "The tone actually used",
"notes": "Very brief note on how the email satisfied the request"
}
```

## Strategy A Baseline Prompt

```text
Write a professional English email based on the following information.
Intent: {{intent}}
Key Facts: {{key_facts}}
Tone: {{tone}}
Include a subject line and email body.
```

## Repair Prompt Template

```text
You are improving a generated professional email.
Original Input:
Intent: {{intent}}
Key Facts: {{key_facts}}
Tone: {{tone}}
Previous Generated Email:
{{generated_email}}
Problems Found:
{{failure_reasons}}
Rewrite the email so that:
1. Every missing fact is included accurately.
2. The requested tone is improved.
3. The structure remains professional.
4. Unsupported or invented details are removed.
5. The result is concise and polished.
Return only valid JSON using the same schema as the generation prompt.
```



## Custom Metrics
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


## Raw Evaluation Data
- CSV: `E:/web development project 2026/Email Generation Assistant/reports/evaluation_results.csv`
- JSON: `E:/web development project 2026/Email Generation Assistant/reports/evaluation_results.json`

## Comparative Analysis
# Model/Strategy Comparison Summary

## Winner
Based on the evaluation across 10 scenarios, advanced performed better overall.

## Metric Results
- Fact Recall and Integration: Strategy A = 9.29, Strategy B = 9.67
- Tone and Audience Fit: Strategy A = 7.93, Strategy B = 8.05
- Professional Email Quality: Strategy A = 7.65, Strategy B = 8.85
- Overall Average: Strategy A = 8.29, Strategy B = 8.86

## Biggest Failure Mode
simple mainly failed on fact coverage and consistency: 2 of 10 samples had missing or weakly integrated facts.

## Production Recommendation
Use advanced for production. It achieved the strongest overall average (8.86/10) and should remain paired with the quality checker and repair loop.


## PDF Export
PDF generation is not automated in this repository. Export this Markdown file to PDF with one of these commands:

```bash
pandoc reports/final_report.md -o reports/final_report.pdf
# or use VS Code Markdown Preview: Open Preview -> Print -> Save as PDF
```
