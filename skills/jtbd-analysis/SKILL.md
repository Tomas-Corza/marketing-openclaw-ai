---
name: jtbd-analysis
description: Analyze marketing experiments using Jobs-to-be-Done motivations and compare message performance.
---

# Jobs-to-be-Done Analysis

Use this skill when the user wants to:

- Analyze JTBD marketing experiments
- Compare messaging based on customer motivations
- Evaluate email click-rate performance
- Identify promising hypotheses for future tests

## Procedure

1. Identify the customer job and experiment objective.
2. Confirm that the dataset is authorized for analysis.
3. For CSV files containing variant, job, delivered, and clicks, run:

   python3 jtbd/analyze.py <csv_file>

4. Compare observed click rates across variants.
5. Explain the results in plain language.
6. Suggest follow-up experiments.

## Interpretation rules

- Higher observed click rates do not establish causation.
- Do not claim statistical significance without testing it.
- Distinguish customer motivations from validated customer needs.
- Never invent experiment results.
- Do not access confidential business data without authorization.
- Ask for approval before modifying campaigns or sending messages.
