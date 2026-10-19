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

<!-- Each label has a definition and two examples from the labeled CVE records. -->

### `LOW`

**Definition:** Vulnerabilities with comparatively limited impact or constrained exploitation conditions.

**Examples:**
- `CVE-2026-11251`: “insufficient policy enforcement in password manager ... allowed a remote attacker who had compromised the renderer process to bypass discretionary access control”
- `CVE-2026-11240`: “insufficient validation of untrusted input in loader ... allowed a remote attacker who had compromised the renderer process to bypass site isolation”

### `MEDIUM`

**Definition:** Vulnerabilities that create a meaningful security risk, but whose impact or exploitability is more constrained than HIGH or CRITICAL.

**Examples:**
- `CVE-2026-5146`: “improper access control in the notification management endpoints ... allows an unauthenticated attacker to modify or delete arbitrary user notification records”
- `CVE-2026-5900`: “policy bypass in downloads ... allowed a remote attacker to bypass ... multi-download protections”

### `HIGH`

**Definition:** Serious vulnerabilities with substantial impact, such as remotely triggered memory corruption or code execution, but below the CRITICAL CVSS severity band.

**Examples:**
- `CVE-2026-5915`: “insufficient validation of untrusted input in webml ... allowed a remote attacker to perform an out of bounds memory write”
- `CVE-2026-5883`: “use after free in media in google chrome ... allowed a remote attacker to execute arbitrary code inside a sandbox”

### `CRITICAL`

**Definition:** The highest severity category, for vulnerabilities with the potential for especially severe compromise, including sandbox escape or bypass of core security controls.

**Examples:**
- `CVE-2026-11061`: “type confusion in angle ... allowed a remote attacker to potentially perform a sandbox escape”
- `CVE-2026-5426`: “hard-coded asp.net/iis machinekey value ... allows adversaries to circumvent viewstate validation mechanisms”

### The hardest boundary

**Which two labels:**
HIGH and CRITICAL
**The decision rule I used every time:**
The description alone does not decide this boundary: I use the record's official CVSS `baseSeverity`. For CVSS v3.x and v4, HIGH corresponds to a base score of 7.0–8.9 and CRITICAL to 9.0–10.0. If the same terms (such as “arbitrary code execution” or “sandbox escape”) appear in both, I keep the severity recorded by CVSS rather than relabeling from keywords.

---

## The Dataset

<!-- Where you collected from, how you labelled, your counts, and three hard
     cases. -->

**Where the posts came from:**
The dataset was extracted from the public CVE JSON dump in `data/CVE_2026`. Each row combines a CNA vulnerability description with CVSS severity metadata in the CVE record; CVE and NVD feeds provide the source records ([NVD data feeds](https://nvd.nist.gov/vuln/data-feeds)).
**How I labelled them:** <!-- Cold first? Pre-labelled with AI and corrected?
Say so plainly — the disclosure is required, not penalised. -->
The labels were extracted automatically from the CVSS `baseSeverity` field in the first ADP entry; CVSS v4.0, v3.1, v3.0, and v2.0 metric fields are checked in that order. Keeping the first ADP preserves the source-selection policy used to build this dataset while supporting CVSS schema versions beyond v3.1. The description comes from the CNA description field. I did not manually relabel the records. `data/extract_labels.py` normalizes descriptions, keeps one row per cleaned-text/severity pair, and writes `labels.csv` with `text`, `label`, and `note` columns. Identical descriptions carrying different official severities are retained rather than arbitrarily choosing one label.
**Counts per label:**

|  Label     | Count | Share |
|  ---       | ---   | ---   |
|  LOW       | 117   | 3.7%  |
|  MEDIUM    | 1319  | 41.5% |
|  HIGH      | 1284  | 40.4% |
|  CRITICAL  | 455   | 14.3% |
| **Total**  | 3175  | 100%  |

**Three hard cases**

<!-- Any post that made you pause: what it was, which two labels it could have
     been, and what you chose. These are worth more than the easy 190. -->

**1.**
> *The post:*
>`CVE-2026-5883`: “use after free in media in google chrome ... allowed a remote attacker to execute arbitrary code inside a sandbox via a crafted html page.”
> *Could have been:*
> CRITICAL
> *I chose, because:*
> HIGH. The official CVSS `baseSeverity` is HIGH; code execution language alone does not override that label.

**2.**
> *The post:*
>`CVE-2026-11061`: “type confusion in angle ... allowed a remote attacker to potentially perform a sandbox escape via a crafted html page.”
> *Could have been:*
> HIGH
> *I chose, because:*
> CRITICAL. The official CVSS `baseSeverity` is CRITICAL, even though “sandbox escape” also appears in HIGH descriptions.

**3.**
> *The post:*
>`CVE-2026-11068`: “use after free in websockets in google chrome ... allowed a remote attacker to execute arbitrary code inside a sandbox via a crafted html page.”
> *Could have been:*
> CRITICAL
> *I chose, because:*
> HIGH. The official CVSS `baseSeverity` is HIGH; the description's exploit language is not a substitute for its CVSS score.
---

## The Training Run

<!-- Your starting model, your settings, and anything you changed and why. -->

**Base model:** `distilbert-base-uncased`

**Settings:** Learning rate `2e-5`, batch size `16`, seed `42`, maximum sequence length `128`. The first run trained for 3 epochs. For the second run I changed only the epoch count, from 3 to 6.

**Split sizes:** 2,221 train / 477 validation / 477 test (70% / 15% / 15%, stratified). The 477-row test split contains LOW 18, MEDIUM 198, HIGH 193, and CRITICAL 68; no class has fewer than 8 test examples.

**Held-out test results** (seed 42; recorded in [`results.json`](results.json)): accuracy `0.633124`, macro F1 `0.420202`.

| Label | Test support | Test F1 |
|---|---:|---:|
| LOW | 18 | 0.240000 |
| MEDIUM | 198 | 0.732394 |
| HIGH | 193 | 0.651270 |
| CRITICAL | 68 | 0.057143 |

**Validation history — 3 epochs:**

| Epoch | Training loss | Validation loss | Accuracy | Macro F1 |
|---:|---:|---:|---:|---:|
| 1 | 0.867700 | 0.888156 | 0.631027 | 0.346474 |
| 2 | 0.818700 | 0.818471 | 0.675052 | 0.516893 |
| 3 | 0.701500 | 0.811576 | 0.664570 | 0.523919 |

**Validation history — 6 epochs:**

| Epoch | Training loss | Validation loss | Accuracy | Macro F1 |
|---:|---:|---:|---:|---:|
| 1 | 0.855800 | 0.878345 | 0.633124 | 0.347926 |
| 2 | 0.807200 | 0.808116 | 0.672956 | 0.548618 |
| 3 | 0.681400 | 0.800203 | 0.675052 | 0.593533 |
| 4 | 0.665900 | 0.802945 | 0.672956 | 0.609411 |
| 5 | 0.551900 | 0.834772 | 0.670860 | 0.587709 |
| 6 | 0.488100 | 0.843396 | 0.677149 | 0.607847 |

The longer run's final validation accuracy was 0.677149 versus 0.664570 after 3 epochs, and its final macro F1 was 0.607847 versus 0.523919 (+0.083928). The longer run reached its best macro F1 at epoch 4 (0.609411), while its lowest validation loss was at epoch 3 (0.800203). Validation loss then rose through epoch 6 as training loss continued to fall, suggesting overfitting after about epoch 3; early stopping at epoch 3–4 would be reasonable depending on whether loss or macro F1 is prioritized. The held-out test evaluation is recorded in [`results.json`](results.json). Both complete validation histories and run settings are recorded in [`training_runs.json`](training_runs.json).

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



## Stretch Features

**Fourth label:** CRITICAL is the stretch addition to the three-label version. It captures the most severe CVSS cases separately instead of merging them into HIGH, preserving a distinction the original three labels would have missed.

**Second training run:** I increased the epoch count from 3 to 6 while holding the model, learning rate, batch size, seed, and data splits constant. The run histories and settings are in [`training_runs.json`](training_runs.json). Macro F1 improved from 0.523919 at epoch 3 of the first run to a peak of 0.609411 at epoch 4 of the second run; validation loss was lowest at epoch 3 of the longer run and then increased, so additional epochs improved the class-balanced score but also showed an overfitting signal.

---

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
