# Paper Refereeing Workflow

This workflow enables deep, autonomous refereeing of academic papers. The goal is thorough, meticulous review that catches errors in notation, logic, proofs, empirical strategy, and data.

## Starting a Review

When asked to referee a paper:

1. **Create the report file**: `referee_reports/<paper_name>.md`
2. **Create tasks** for each phase using the task system
3. **Work autonomously** through all phases
4. **Update the report** as findings accumulate

---

## Phase 1: First Pass (Global Understanding)

**Objective**: Understand the paper's structure, contribution, and methodology.

### Tasks:
- [ ] Read the entire paper end-to-end
- [ ] Write a 1-paragraph summary of the main contribution
- [ ] Identify paper type: pure theory / pure empirical / mixed
- [ ] List the key claims (what the paper asserts it proves/shows)
- [ ] Map the logical structure (which sections depend on which)
- [ ] Note first impressions and areas of concern

### Output:
Add to report under `## 1. Overview`:
- Summary
- Paper type
- Key claims inventory
- Structure map
- Initial concerns

---

## Phase 2: Decomposition

**Objective**: Break the paper into auditable units for deep review.

### Standard Decomposition:

```
Paper
├── Abstract & Introduction
│   └── Claims inventory (promises made)
├── Literature Review
│   └── Positioning and gaps claimed
├── Model / Theoretical Framework
│   ├── Setup (primitives, timing, agents)
│   ├── Assumptions (stated and implicit)
│   ├── Definitions
│   ├── Propositions / Theorems / Lemmas
│   └── Proofs (each one separately)
├── Empirical Strategy (if applicable)
│   ├── Identification strategy
│   ├── Estimating equations
│   ├── Data description
│   └── Sample construction
├── Results
│   ├── Main results (each table/figure)
│   ├── Robustness checks
│   └── Heterogeneity analysis
├── Discussion / Conclusion
│   └── Claims vs. evidence reconciliation
└── Appendices
    ├── Additional proofs
    ├── Data appendix
    └── Additional results
```

### Tasks:
- [ ] Create a task for each auditable unit identified
- [ ] Note dependencies between units (e.g., Proposition 2 uses Lemma 1)

---

## Phase 3: Deep Audits

For each unit, apply the relevant checklists below. Create sub-tasks as needed.

### 3.1 Notation Audit

For every section with mathematical content:

- [ ] **Definition check**: Is every symbol defined before first use?
- [ ] **Consistency**: Same symbol always means the same thing?
- [ ] **No overloading**: Different concepts use different symbols?
- [ ] **Subscript/superscript logic**: Consistent indexing conventions?
- [ ] **Sets vs. elements**: Clear distinction (e.g., $x \in X$)?
- [ ] **Timing notation**: Consistent (t, t+1, etc.)?
- [ ] **Expectation/probability**: Conditioning clear? Measure specified?

### 3.2 Proof Audit

For each proof:

- [ ] **Statement clarity**: Is what's being proved precisely stated?
- [ ] **Assumptions invoked**: Are all assumptions used actually stated earlier?
- [ ] **Step validity**: Does each step follow logically from previous?
- [ ] **Gaps**: Are there jumps that require justification?
- [ ] **Edge cases**: Are boundary conditions handled?
- [ ] **Contradiction/contrapositive**: If used, is the logic correct?
- [ ] **Induction**: Base case and inductive step both present and correct?
- [ ] **Existence vs. uniqueness**: If both claimed, both proved?
- [ ] **Quantifier order**: $\forall \exists$ vs. $\exists \forall$ correct?

### 3.3 Model/Theory Audit

- [ ] **Primitives**: All primitives clearly defined?
- [ ] **Timing**: Sequence of events unambiguous?
- [ ] **Information structure**: Who knows what when?
- [ ] **Equilibrium concept**: Clearly defined? Standard or custom?
- [ ] **Existence**: Is equilibrium existence established?
- [ ] **Uniqueness**: Claimed? Proved?
- [ ] **Comparative statics**: Sign claims match derivations?
- [ ] **Regularity conditions**: Sufficient for results?

### 3.4 Identification Audit (Empirical Papers)

- [ ] **Causal claim**: What causal effect is claimed?
- [ ] **Identification strategy**: What provides exogenous variation?
- [ ] **Key assumption**: What's the identifying assumption?
- [ ] **Plausibility**: Is the assumption plausible in context?
- [ ] **Testable implications**: Are auxiliary predictions tested?
- [ ] **Threats**: What could violate identification? Addressed?
- [ ] **SUTVA/spillovers**: Treatment of one unit affects others?
- [ ] **Selection**: Into treatment? Into sample?
- [ ] **Parallel trends**: If DiD, is this tested/discussed?
- [ ] **Exclusion restriction**: If IV, is this plausible?
- [ ] **First stage**: If IV, is it strong enough?
- [ ] **Monotonicity**: If LATE, is this discussed?

### 3.5 Data Audit

- [ ] **Source**: Where does the data come from?
- [ ] **Sample construction**: How is the sample built?
- [ ] **Time period**: What period? Why?
- [ ] **Unit of observation**: Clear and consistent?
- [ ] **Variable definitions**: All variables clearly defined?
- [ ] **Missing data**: How handled?
- [ ] **Outliers**: Treatment of outliers?
- [ ] **Summary statistics**: Do they make sense?
- [ ] **External validity**: How representative is the sample?
- [ ] **Replicability**: Could someone replicate this?

### 3.6 Results Audit

For each table/figure:

- [ ] **Matches text**: Do numbers in text match tables?
- [ ] **Specification**: Is the estimating equation clear?
- [ ] **Standard errors**: Clustering appropriate? Robust?
- [ ] **Controls**: What's controlled for? Why?
- [ ] **Sample size**: Consistent across specifications?
- [ ] **Magnitude interpretation**: Are effect sizes interpreted sensibly?
- [ ] **Statistical vs. economic significance**: Both discussed?
- [ ] **Multiple testing**: Adjustment needed?

### 3.7 Robustness Audit

- [ ] **Alternative specifications**: Do results hold?
- [ ] **Alternative samples**: Sensitive to sample choice?
- [ ] **Alternative measures**: Different variable definitions?
- [ ] **Placebo tests**: If applicable, do they pass?
- [ ] **Falsification tests**: Appropriate checks run?
- [ ] **Sensitivity analysis**: To key assumptions?

### 3.8 Logic & Argumentation Audit

- [ ] **Claims vs. evidence**: Does evidence support claims made?
- [ ] **Overclaiming**: Are conclusions too strong for results?
- [ ] **Alternative explanations**: Considered and ruled out?
- [ ] **Literature engagement**: Fair representation of prior work?
- [ ] **Contribution clarity**: What's new vs. what's known?

### 3.9 Literature & Citation Audit

This audit requires active online research. Use WebSearch to verify and expand.

#### A. Citation Accuracy Check

For each key citation (especially those supporting central claims):

- [ ] **Search the cited paper**: Use WebSearch to find the original paper
- [ ] **Verify the claim**: Does the cited paper actually say what the author claims?
- [ ] **Context accuracy**: Is the citation taken out of context?
- [ ] **Version check**: Is the author citing the correct/final version?
- [ ] **Author names**: Are author names and year correct?
- [ ] **Misattribution**: Are ideas attributed to the right source?

**Common citation errors to catch:**
- Citing a paper for claim X when it actually argues the opposite
- Citing a secondary source when the original is available
- "String citations" that don't engage with the actual content
- Citing working papers when published versions exist

#### B. Literature Gap Analysis

Actively search for missing relevant work:

- [ ] **Core topic search**: WebSearch the paper's main topic + "economics"/"econometrics"/relevant field
- [ ] **Methodology search**: Search for other papers using the same identification strategy or method
- [ ] **Competing papers**: Search for papers with similar research questions
- [ ] **Recent work**: Search for papers published in the last 2-3 years that the authors may have missed
- [ ] **Key author search**: Search for recent work by major figures in the relevant subfield
- [ ] **Seminal works**: Are foundational papers in the area cited?
- [ ] **Handbook chapters**: Are relevant handbook chapters or surveys cited?

**Search strategies:**
```
"[main topic]" "economics" site:nber.org OR site:ssrn.com OR site:aeaweb.org
"[identification strategy]" "[similar context]" economics
"[dependent variable]" "[key mechanism]" empirical
author:"[key researcher in field]" [topic]
```

#### C. Contribution Positioning

- [ ] **Novelty claim check**: Search to verify the claimed contribution is actually novel
- [ ] **Concurrent work**: Are there concurrent/simultaneous papers making similar contributions?
- [ ] **Working paper predecessors**: Did a working paper version of a cited paper already establish this?
- [ ] **Related fields**: Is there relevant work in adjacent fields (political science, sociology, etc.)?

#### D. Key Papers to Verify

Create a list of the 5-10 most important citations and verify each one:

| Citation | Claim in Paper | Actual Content | Accurate? |
|----------|---------------|----------------|-----------|
| ... | ... | ... | Y/N |

---

## Phase 3.5: Online Verification Tasks

For papers requiring deep verification, create specific research tasks:

### Task Template: Citation Verification
```
Task: Verify citation [Author Year]
- Search for the paper online
- Read abstract and relevant sections
- Compare to how it's cited in the paper under review
- Note any discrepancies
```

### Task Template: Literature Gap Search
```
Task: Search for missing literature on [topic]
- Search: "[topic keywords]" economics/finance/etc.
- Search: NBER working papers on [topic]
- Search: Recent AER/QJE/REStud/JF on [topic]
- Note relevant papers not cited
```

### Task Template: Methodological Precedent Search
```
Task: Find papers using [identification strategy] in [context]
- Search for similar empirical approaches
- Note how they handle common threats
- Compare robustness checks performed
```

---

## Phase 4: Cross-Cutting Checks

After all units are audited:

- [ ] **Abstract accuracy**: Does abstract match actual findings?
- [ ] **Introduction promises**: All promises in intro fulfilled?
- [ ] **Internal consistency**: No contradictions across sections?
- [ ] **Forward/backward references**: All references resolve correctly?
- [ ] **Figure/table references**: All cited? Numbers correct?
- [ ] **Equation numbering**: Consistent and correct?
- [ ] **Bibliography**: All citations present? Formats consistent?
- [ ] **Appendix references**: Main text references to appendix correct?

---

## Phase 5: Synthesis

### Classify Findings by Severity:

**Critical** (potentially fatal flaws):
- Proofs that are incorrect
- Identification that fails
- Data errors that affect main results
- Logical contradictions in core arguments

**Major** (significant issues requiring revision):
- Missing robustness checks
- Unclear identification assumptions
- Notation inconsistencies that confuse
- Overclaiming relative to evidence
- Missing literature engagement

**Minor** (should be fixed but not fundamental):
- Typos and small notation issues
- Missing references
- Presentation improvements
- Clarifications needed

### Write the Report:

Structure the final report as:

```markdown
# Referee Report: [Paper Title]

## Executive Summary
[2-3 paragraph overview: contribution, main concerns, recommendation]

## 1. Overview
[From Phase 1]

## 2. Critical Issues
[List with detailed explanation of each]

## 3. Major Issues
[List with detailed explanation of each]

## 4. Minor Issues
[List, can be more concise]

## 5. Detailed Audit Notes
### 5.1 Theory/Model
### 5.2 Proofs
### 5.3 Empirical Strategy
### 5.4 Data
### 5.5 Results
### 5.6 Presentation

## 6. Constructive Suggestions

### 6.1 Methodological Improvements
[Specific suggestions to strengthen identification, address threats, add robustness]

### 6.2 Theoretical Extensions
[Natural extensions, relaxed assumptions, additional results that would strengthen the contribution]

### 6.3 Data and Measurement
[Better data sources, alternative variable constructions, additional tests]

### 6.4 Literature and Framing
[Missing citations to add, better positioning, clearer contribution statement]

### 6.5 Presentation and Clarity
[Structural improvements, better exposition, figures/tables to add]

## 7. Missing Literature
[Papers found via online search that should be cited, with brief explanation of relevance]

## Appendix: Audit Trail
[Summary of all units checked and findings per unit]

## Appendix: Citation Verification Log
[Results of citation accuracy checks - which citations were verified, any discrepancies found]
```

---

## Task Management

Use the task system throughout:

1. **Phase 1**: Single task for first pass
2. **Phase 2**: Task for decomposition, then create child tasks for each unit
3. **Phase 3**: Each unit is a task; mark complete when fully audited
4. **Phase 4**: Single task for cross-cutting checks
5. **Phase 5**: Single task for synthesis

Update the report file continuously as findings emerge—don't wait until the end.

---

## Notes

- **Be thorough**: The goal is to catch everything. Take your time on each unit.
- **Be specific**: "Proof unclear" is not helpful. "Step 3 of Proof of Proposition 2 assumes X but X was not established" is helpful.
- **Be constructive**: Identify problems but also suggest solutions where possible.
- **Track your work**: Update tasks and the report as you go.
- **Use Overleaf tools**: If the paper is in Overleaf, use those tools to read/navigate.

---

## Online Research Guidelines

### Using WebSearch for Literature Review

**Effective search queries:**

1. **Finding related papers:**
   - `"[exact phrase from paper's contribution]" economics`
   - `[author name] [topic] working paper`
   - `site:nber.org "[topic]"` or `site:ssrn.com "[topic]"`

2. **Verifying citations:**
   - `"[author] [year]" "[key phrase the paper attributes to them]"`
   - `"[paper title]" abstract`

3. **Finding methodological precedents:**
   - `"[identification strategy]" "[similar industry/context]"`
   - `"regression discontinuity" "[topic]"` (substitute actual method)

4. **Finding recent work:**
   - `[topic] 2024 OR 2025 economics working paper`
   - `[topic] forthcoming journal economics`

### What to Look For in Literature Gaps

**Red flags that literature is missing:**
- Paper claims "first to study X" but search reveals prior work
- No citations from last 3 years in an active research area
- Major researchers in subfield not cited
- No engagement with critique/counterargument papers
- Missing foundational/seminal works

**Where missing literature matters most:**
- When it challenges the claimed contribution
- When it uses a similar identification strategy (robustness comparison)
- When it provides alternative explanations for the results
- When it offers data or methods that could strengthen the paper

### Citation Verification Priority

Focus verification efforts on citations that:
1. Support the paper's main identification assumptions
2. Justify key modeling choices
3. Are used to dismiss alternative explanations
4. Support controversial or surprising claims
5. Are from working papers (may have been revised)

### Documenting Online Research

For each search conducted, log:
- Query used
- Key results found
- Relevance to the paper
- Action taken (added to missing literature, verified citation, etc.)

This creates an audit trail showing the review was thorough.
