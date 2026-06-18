# Final Report: Email Generation Assistant

Generated: June 19, 2026

This report is structured to match the assessment deliverables exactly: prompt template, custom metrics, raw evaluation data, and comparative analysis.

## 1. Prompt Template Used

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

## 2. Definitions and Logic for the 3 Custom Metrics

### Fact Recall and Integration Score
- Scale: 0-10
- Definition: Checks whether every required key fact appears correctly and naturally in the email.
- Logic: 70% deterministic fact presence and 30% LLM natural-integration judgment when the judge is available.

### Tone and Audience Fit Score
- Scale: 0-10
- Definition: Rates whether the generated email matches the requested tone while staying professional.
- Logic: LLM-as-a-judge score with deterministic tone fallback.

### Professional Email Quality Score
- Scale: 0-10
- Definition: Rates subject, greeting, body clarity, CTA, closing, conciseness, grammar, and fluency.
- Logic: 40% deterministic structure checks and 60% LLM quality judgment when the judge is available.

## 3. Raw Evaluation Data (CSV/JSON Output)

Raw data files generated by the evaluation script:

- CSV output: `E:/web development project 2026/Email Generation Assistant/reports/evaluation_results.csv`
- JSON output: `E:/web development project 2026/Email Generation Assistant/reports/evaluation_results.json`

Validation summary:

- Total result rows: 20
- Unique scenarios: 10
- Compared strategies: `simple`, `advanced`
- Custom metrics per row: 3

### Average Scores

| Strategy | Fact Recall | Tone Fit | Email Quality | Overall |
|---|---:|---:|---:|---:|
| Simple | 9.29 | 7.93 | 7.65 | 8.29 |
| Advanced | 9.67 | 8.05 | 8.85 | 8.86 |

### Raw Score Table

| Scenario | Strategy | Intent | Tone | Fact Recall | Tone Fit | Email Quality | Overall |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | advanced | Follow up after a client meeting | Formal | 9.70 | 8.00 | 8.80 | 8.83 |
| 1 | simple | Follow up after a client meeting | Formal | 9.40 | 6.80 | 6.87 | 7.69 |
| 2 | advanced | Request missing proposal details | Polite and clear | 9.70 | 8.00 | 8.80 | 8.83 |
| 2 | simple | Request missing proposal details | Polite and clear | 9.70 | 8.00 | 8.07 | 8.59 |
| 3 | advanced | Urgent project deadline reminder | Urgent but professional | 9.70 | 8.40 | 9.40 | 9.17 |
| 3 | simple | Urgent project deadline reminder | Urgent but professional | 9.70 | 8.40 | 8.07 | 8.72 |
| 4 | advanced | Apologize for a service delay | Empathetic | 9.40 | 7.80 | 8.80 | 8.67 |
| 4 | simple | Apologize for a service delay | Empathetic | 7.95 | 8.40 | 8.07 | 8.14 |
| 5 | advanced | Schedule an interview | Formal | 9.40 | 6.80 | 8.20 | 8.13 |
| 5 | simple | Schedule an interview | Formal | 9.40 | 6.80 | 6.87 | 7.69 |
| 6 | advanced | Payment reminder | Polite but firm | 9.70 | 8.32 | 8.80 | 8.94 |
| 6 | simple | Payment reminder | Polite but firm | 9.70 | 8.32 | 6.87 | 8.30 |
| 7 | advanced | Internal project status update | Concise executive | 9.70 | 8.32 | 7.53 | 8.52 |
| 7 | simple | Internal project status update | Concise executive | 9.70 | 8.32 | 8.07 | 8.70 |
| 8 | advanced | Networking introduction | Friendly professional | 10.00 | 8.50 | 10.00 | 9.50 |
| 8 | simple | Networking introduction | Friendly professional | 9.70 | 7.88 | 7.47 | 8.35 |
| 9 | advanced | Request approval for budget | Persuasive | 9.70 | 8.00 | 9.40 | 9.03 |
| 9 | simple | Request approval for budget | Persuasive | 9.70 | 8.00 | 8.07 | 8.59 |
| 10 | advanced | Respond to customer complaint | Calm and empathetic | 9.70 | 8.40 | 8.80 | 8.97 |
| 10 | simple | Respond to customer complaint | Calm and empathetic | 7.95 | 8.40 | 8.07 | 8.14 |

## 4. Comparative Analysis Summary (Section 3)

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

### Final Recommendation

Use the **advanced** strategy for production. Use advanced for production. It achieved the strongest overall average (8.86/10) and should remain paired with the quality checker and repair loop.
