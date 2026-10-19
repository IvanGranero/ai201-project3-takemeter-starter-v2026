# TakeMeter

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, the
> notebook, the baseline, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> head -5 data/practice_labels.csv     # the shape your labels.csv needs
> ```
>
> Then open `takemeter.ipynb` **in this folder** — in VS Code, or with
> `jupyter notebook` if you prefer. Pick the kernel: the `.venv` inside this
> project. Run section 1, which reports the hardware you'll be training on.
> Everything else waits until you have data.
>
> Nothing to upload, nothing to connect, no accounts and no keys. The notebook
> runs on your machine and writes next to your code.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     Unit 5 asks for the first five sections. Unit 6 adds the five below them.

     Everything is pasted as TEXT. No screenshots, no images.

     ⚠️ The confusion matrix especially. The notebook prints one as a markdown
     table, ready to copy. A screenshot of a matrix earns nothing. Paste the
     table.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 5 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Your community, and what your classifier sorts posts into. Three or four
     sentences. -->
This project trains a DistilBERT text classifier to predict the CVSS severity of a software vulnerability based solely on its natural language description. The dataset consists of CVE records collected from public vulnerability disclosures and automatically labeled using the CVSS severity provided in each record. The classifier learns patterns associated with LOW, MEDIUM, HIGH, and CRITICAL vulnerabilities and can be used to estimate severity from previously unseen descriptions.

---

## Label Taxonomy

<!-- Each label: a one-sentence definition and two real examples from your
     reading. Then your decision rule for the hardest boundary.

     The decision rule is worth a point on its own and it's the thing most
     people leave out. Every taxonomy has a hardest boundary. Name yours. -->

### `label_one`
LOW
**Definition:**
Vulnerabilities with limited security impact, requiring significant constraints or resulting in minimal compromise of confidentiality, integrity, or availability.
**Example 1:**
>Use after free in gpu in google chrome prior to allowed a remote attacker who had compromised the renderer process to perform an out of bounds memory write via a crafted html page.
**Example 2:**
>CVEs in the dataset labeled with CVSS severity LOW, typically involving limited impact or highly constrained exploitation conditions.

### `label_two`
MEDIUM
**Definition:**
Vulnerabilities that present a meaningful security risk but usually require user interaction, specific conditions, or provide only partial impact.
**Example 1:**
>A use-after-free issue was addressed with improved memory management. This issue is fixed in iOS and iPadOS ...
**Example 2:**
>This issue was addressed with additional entitlement checks. An app may be able to circumvent app restrictions...

### `label_three`
HIGH
**Definition:**
Vulnerabilities that can significantly impact confidentiality, integrity, or availability and are often remotely exploitable.
**Example 1:**
>Use-after-free in the DOM: Networking component. This vulnerability was fixed in Firefox ...
**Example 2:**
>Integer overflow in the audio/video component. This vulnerability was fixed in Firefox 148...

### `label_four`
CRITICAL
**Definition:**
Vulnerabilities that can lead to severe compromise of a system, such as remote code execution, sandbox escape, or full system takeover.
**Example 1:**
>Use-after-free in the JavaScript engine component. This vulnerability was fixed in Firefox 148...
**Example 2:**
>Sandbox escape due to incorrect boundary conditions in the telemetry component in external software...

### The hardest boundary

**Which two labels:**
HIGH and CRITICAL
**The decision rule I used every time:**
<!-- e.g. "If the post names a specific checkable fact, it's `analysis`, even
     if the tone is heated." -->
For CVSS severity classification, the hardest boundary is HIGH vs CRITICAL because the text often contains the same keywords:
use-after-free
type confusion
arbitrary code execution
sandbox escape
memory corruption

Yet some are labeled HIGH and others CRITICAL.

---

## The Dataset

<!-- Where you collected from, how you labelled, your counts, and three hard
     cases. -->

**Where the posts came from:**
The dataset was collected from CVE JSON records containing vulnerability descriptions and CVSS metadata. Each sample consists of the vulnerability description extracted from the CVE record and the corresponding CVSS severity label. Reference https://nvd.nist.gov/vuln/data-feeds.
**How I labelled them:** <!-- Cold first? Pre-labelled with AI and corrected?
Say so plainly — the disclosure is required, not penalised. -->
The data was automatically labeled using the CVSS baseSeverity field already present in each CVE record. No manual relabeling was performed. The labels were extracted programmatically and converted to numeric classes.
**Counts per label:**

|  Label     | Count | Share |
|  ---       | ---   | ---   |
|  LOW       | 117   | 3.7%  |
|  MEDIUM    | 1319  | 41.5% |
|  HIGH      | 1284  | 40.4% |
|  CRITICAL  | 455   | 14.3# |
| **Total**  | 3175  | 100%  |

**Three hard cases**

<!-- Any post that made you pause: what it was, which two labels it could have
     been, and what you chose. These are worth more than the easy 190. -->

**1.**
> *The post:*
>"use after free in media in google chrome prior to allowed a remote attacker to execute arbitrary code inside a sandbox via a crafted html page."
> *Could have been:*
> CRITICAL
> *I chose, because:*
> HIGH, If the record is scored HIGH, I assign HIGH even when the description contains terms such as "arbitrary code execution", "use-after-free", "type confusion", or "memory corruption".

**2.**
> *The post:*
>"type confusion in angle in google chrome prior to allowed a remote attacker to potentially perform a sandbox escape via a crafted html page."
> *Could have been:*
> HIGH
> *I chose, because:*
> CRITICAL, If the official CVSS severity in the CVE record is CRITICAL, I assign the CRITICAL label. 

**3.**
> *The post:*
>"use after free in websockets in google chrome prior to allowed a remote attacker to execute arbitrary code inside a sandbox via a crafted html page."
> *Could have been:*
> CRITICAL
> *I chose, because:*
> HIGH, The official CVSS severity always overrides my interpretation of the vulnerability text.
---

## The Training Run

<!-- Your starting model, your settings, and anything you changed and why. -->

**Base model:**

**Settings:** <!-- epochs, learning rate, batch size, seed -->

**Anything I changed from the defaults, and why:**

**Split sizes:** <!-- train / val / test, and per-label counts in the test
split. If a label had fewer than about 8 in test, say so — it explains a lot
of next unit's variance. -->



---

## How I Used AI

<!-- Two specific moments — what you asked, what came back, what you changed.

     ⚠️ Plus disclosure of any pre-labelling. If you had a model pre-label a
     batch and then read and corrected every one, say that. It's an allowed
     workflow and disclosing it costs you nothing. Not disclosing it is the
     problem. -->

**Moment 1**

- *What I asked for:* Help me create a script to extract labels from the NVD database.
- *What came back:* A script for retrieving and organizing the existing NVD labels.
- *What I changed:* I reviewed and adapted the script for my project and checked that it extracted the labels I needed.

**Moment 2**

- *What I asked for:* Given my definitions, write eight posts that sit on the boundaries between the categories.
- *What came back:* Eight boundary-case posts to test whether my definitions led to clear classifications.
- *What I changed:* I used the examples to identify ambiguous cases and refine my definitions before labeling a larger set.

**Pre-labelling disclosure:** AI helped me extract existing labels from the NVD database and generate test examples. I did not use it to pre-label my data.

<!-- ═══════════════════════ UNIT 6 — THE TEST ═══════════════════════

     Don't fill these in during unit 5.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Baseline vs. Trained

<!-- Both models on the same posts. `python baseline.py --trained results.json`
     prints this table for you. -->

| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy |  |  |  |
| Macro F1 |  |  |  |
| F1 — `label_one` |  |  |  |
| F1 — `label_two` |  |  |  |

**What I predicted before I looked:**
<!-- Milestone 1 asks you to write this BEFORE seeing the trained numbers. A
     prediction made afterwards isn't one. -->

**What the gap actually means:**
<!-- If the baseline matched your trained model, your fine-tuning added
     nothing — and that is a real finding, not a failure. Say it plainly. -->



---

## Run Log — Before

<!-- Five criteria across three seeds. The notebook's section 6 prints the
     spread table; the Target and Verdict columns are yours. -->

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

### Confusion matrix

<!-- ⚠️ TYPED AS A MARKDOWN TABLE. The notebook prints one ready to paste.
     An image of a matrix earns nothing. -->

| true \ predicted |  |  |  |
|---|---|---|---|
| **** |  |  |  |
| **** |  |  |  |
| **** |  |  |  |

**My biggest off-diagonal number, and what it means:**
<!-- Not "the model made mistakes" — WHICH boundary it didn't learn, and which
     direction. "7 real analysis posts were called hot_take and only 3 went the
     other way" is a direction, not just an error rate. -->



---

## Verdicts and Diagnoses

<!-- MET or MISSED against LAST UNIT's target. The target has to hold across
     all three seeds, not turn up sometimes. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**

<!-- For each miss: the cause, and how you know. The four common causes are:
     too few examples for a label, a boundary you applied inconsistently, a
     genuinely hard label pair, and a task the model can't reach from this
     much data.

     ⚠️ Use your agreement report as evidence. It is the only instrument you
     have that can tell a LABELLING problem from a MODEL problem, and this
     section is graded on whether you used it that way. -->



---

## Agreement Report

<!-- Your rate against the staff set, and every disagreement adjudicated.

     Remember you labelled these 30 under the STAFF taxonomy in
     data/staff_taxonomy.md, not your own — so every argument below is made
     from those definitions and those decision rules. -->

**Agreement rate:** ___ / 30 = ___%

<!-- Nobody grades this number. A 60% who argues every disagreement from the
     stated rules beats a 95% who wrote "staff was right" nine times. Several
     of the 30 were chosen because they're genuinely ambiguous — you should be
     winning some of these. -->

**Disagreements**

<!-- Three lines each: the post, both labels, and who you think is right and
     why — grounded in the staff definitions you were both applying.

     Then sort each into one of three piles:
       (a) the rule covered it and I applied it loosely → a consistency problem
       (b) the rule genuinely doesn't say               → a gap in the definitions
       (c) the rule is ambiguous here and my reading is defensible → argue it.
           This is a legitimate win.

     Pile (a) is the one that matters most for your diagnosis: if you applied a
     written rule two different ways on 30 posts, that is direct evidence about
     what you did across your own 200. -->

**1.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**2.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**What the pattern in my disagreements tells me:**



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Run Log — After

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it didn't, say so. Relabelling that didn't help is a genuinely
     interesting result and earns full credit. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped. -->



**The gap between what I meant my labels to capture and what the model
learned:**
<!-- Two sentences. Your confusion matrix is the evidence. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 5

       [ ] criteria.md has five numbered criteria, each naming a NUMBER
       [ ] Each has a reason underneath tied to your data or taxonomy
       [ ] labels.csv: at least 150 rows, text/label/note, ONE file not split
       [ ] No label above 70%
       [ ] All five unit 5 sections have real content
       [ ] Label Taxonomy includes the decision rule for your hardest boundary
       [ ] The Dataset includes three hard cases
       [ ] results.json and test_split.csv committed (the notebook does this)
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 6

       [ ] Baseline vs. Trained table, with your prediction written beforehand
       [ ] Run Log — Before, five criteria across three seeds
       [ ] Confusion matrix TYPED AS A MARKDOWN TABLE
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, using the agreement report as evidence
       [ ] Agreement Report with every disagreement adjudicated
       [ ] One improvement, with Run Log — After
       [ ] What's Still Broken
       [ ] results_three_seeds_before.json, results_three_seeds_after.json,
           baseline_results.json and
           agreement_results.json committed
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
