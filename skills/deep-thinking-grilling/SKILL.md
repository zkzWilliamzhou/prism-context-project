---
name: deep-thinking-grilling
description: Use before committing to a product idea, architecture, or research direction. Generates independent candidates, checks evidence, runs adversarial self-grilling, and records a decision log.
metadata:
  source: local
  license: MIT
  status: original
---

# Deep Thinking and Grilling

Do not pick the first plausible idea. Separate four activities that people
usually blur:

1. **Ideation** creates candidates.
2. **Evidence assessment** checks what is already built.
3. **Adversarial review** attacks the shortlist.
4. **Decision** records a choice, not a consensus.

## Process

1. Write one focal question and list real, assumed, negotiable, and unknown
   constraints.
2. Generate at least 10 candidates independently. Give each an ID, an
   assumption, a prediction, and disconfirming evidence.
3. Preserve a minority view. Do not average away dissent.
4. Search prior art **after** the independent round. Use "not located in a
   bounded search", never "does not exist".
5. Reopen one short ideation round after the evidence check.
6. Assign a reviewer who did not originate each shortlisted idea. Ask what
   observation would make it wrong, what alternative fits the same result, and
   what hidden dependency dominates.
7. Define criteria before scoring. Keep raw ratings and disagreement visible.
8. Record the decision, rejected alternatives, residual uncertainty, owner,
   and revisit trigger.

## Labels

Mark every claim as **idea**, **assumption**, **prediction**, **located
evidence**, or **decision**. Never blur them.

## Output

A Markdown decision log with: focal question, constraints, candidate table,
evidence status, adversarial table, decision, rejected alternatives, success
criteria, and revisit triggers.

## Method credit

Structured ideation here follows the Scientific Agent Skills methodology:
Kassis et al. (2026), arXiv:2609.00065,
https://doi.org/10.48550/arXiv:2609.00065.
