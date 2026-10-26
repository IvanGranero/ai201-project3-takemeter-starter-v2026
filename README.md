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
| Overall accuracy | 0.369 | 0.633 | +0.264 |
| Macro F1 | 0.172 | 0.420 | +0.248 |
| F1 — `CRITICAL` | 0.000 | 0.057 | +0.057 |
| F1 — `HIGH` | 0.073 | 0.651 | +0.578 |
| F1 — `LOW` | 0.053 | 0.240 | +0.187 |
| F1 — `MEDIUM` | 0.561 | 0.732 | +0.172 |

**What I predicted before I looked:**
<!-- Milestone 1 asks you to write this BEFORE seeing the trained numbers. A
     prediction made afterwards isn't one. -->
Accuracy will increase across the four labels with the trained model

**What the gap actually means:**
<!-- If the baseline matched your trained model, your fine-tuning added
     nothing — and that is a real finding, not a failure. Say it plainly. -->
Fine-tuning the model significantly increased accuracy on HIGH labeled items, not so much on CRITICAL labeled items, this will need to be reviewed in order to improve accuracy for CRITICAL items.

---

## Run Log — Before

<!-- Five criteria across three seeds. The notebook's section 6 prints the
     spread table; the Target and Verdict columns are yours. -->

| Measure | Seed 42 | Seed 7 | Seed 2024 | Spread |
|---|---|---|---|---|
| Overall accuracy | 0.646 | 0.702 | 0.660 | 0.057 |
| Macro F1 | 0.492 | 0.614 | 0.553 | 0.121 |
| F1 — `LOW` | 0.231 | 0.467 | 0.345 | 0.236 |
| F1 — `MEDIUM` | 0.736 | 0.783 | 0.727 | 0.057 |
| F1 — `HIGH` | 0.646 | 0.702 | 0.673 | 0.056 |
| F1 — `CRITICAL` | 0.356 | 0.504 | 0.467 | 0.147 |

Accuracy moved 0.057 across seeds. Enough that a criterion landing within that band can't really be called either way.

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.Overall accuracy | ≥ 0.75 on every seed | 0.646 | 0.702 | 0.660 | Missed |
| 2. Macro F1 | ≥ 0.70 on every seed | 	0.492 | 0.614 | 0.553 | Missed |
| 3. Per-label F1  | every label ≥ 0.55 | LOW 0.231, CRITICAL 0.356 fail | LOW 0.467, CRITICAL 0.504 fail | LOW 0.345, CRITICAL 0.467 fail | Missed |
| 4. F1 spread	 | best minus worst label F1 ≤ 0.25 | 0.505 | 0.317 | 0.382 | Missed |
| 5. Confidence | predictions at ≥ 90% confidence correct ≥ 85% of the time | not measurable (top-third proxy 0.868) | not measurable (top-third proxy 0.931) | not measurable (top-third proxy 0.893) | Unverified |

### Confusion matrix

<!-- ⚠️ TYPED AS A MARKDOWN TABLE. The notebook prints one ready to paste.
     An image of a matrix earns nothing. -->

| true \ predicted | LOW | MEDIUM | HIGH | CRITICAL |
|---|---|---|---|---|
| **LOW** | 3 | 11 | 4 | 0 |
| **MEDIUM** | 2 | 162 | 32 | 2 |
| **HIGH** | 0 | 55 | 125 | 13 |
| **CRITICAL** | 3 | 14 | 33 | 18 |

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
| 1 | Overall accuracy | ≥ 0.75 on every seed | **MISSED** | 0.646 / 0.702 / 0.660. All three seeds are below target. The best seed is 0.048 short and the mean (0.669) is 0.081 short, which is more than the 0.057 seed spread, so this is not seed luck. |
| 2 | Macro F1 | ≥ 0.70 on every seed | **MISSED** | 0.492 / 0.614 / 0.553. No seed reaches 0.70. The best is 0.086 short and the mean (0.553) is 0.147 short. The seed spread (0.121) is larger than the best seed's gap, so macro F1 is the criterion where seed luck matters most, but the target has to hold on all three seeds and none gets there. |
| 3 | Per-label F1 | every label ≥ 0.55 on every seed | **MISSED** | MEDIUM (0.727–0.783) and HIGH (0.646–0.702) pass on every seed. LOW (0.231 / 0.467 / 0.345) and CRITICAL (0.356 / 0.504 / 0.467) fail on every seed. Their best scores, 0.467 and 0.504, are still under 0.55. |
| 4 | F1 spread | best label F1 minus worst ≤ 0.25 | **MISSED** | Spread is 0.505 / 0.317 / 0.382. The best label is MEDIUM and the worst is LOW on all three seeds. Even if LOW were lifted to 0.55, CRITICAL becomes the floor and the spread is still 0.380 / 0.279 / 0.260, so this criterion also needs CRITICAL to improve. |
| 5 | Confidence | predictions at ≥ 90% confidence are correct ≥ 85% of the time | **UNVERIFIED** (not MET) | My evaluation saved accuracy by confidence *third* (159 posts each), not at a 0.90 threshold: 0.868 / 0.931 / 0.893. Those clear 0.85, but the top third is not the set of predictions at ≥ 0.90, so I can't call it MET. This is a gap in what I measured, not a missed number. |

**Diagnoses**

<!-- For each miss: the cause, and how you know. The four common causes are:
     too few examples for a label, a boundary you applied inconsistently, a
     genuinely hard label pair, and a task the model can't reach from this
     much data.

     ⚠️ Use your agreement report as evidence. It is the only instrument you
     have that can tell a LABELLING problem from a MODEL problem, and this
     section is graded on whether you used it that way. -->

**How my labels were made changes what a diagnosis can say.** My 3,175 labels are the CVSS `baseSeverity` copied from each CVE record. I did not label them by reading, so "I applied my own boundary two different ways in the training data" is not a cause available to me in the usual sense: the labels follow one fixed rule. The question for each miss is different: can that label be predicted from the description text alone (the model sees 128 tokens)? My own hardest-boundary rule already admits that for HIGH vs CRITICAL it cannot always be: "the description alone does not decide this boundary."

**Diagnosis 1 — Criterion 1 (accuracy): MEDIUM vs HIGH is a genuinely hard pair.**
- *Cause:* the model keeps swapping MEDIUM and HIGH, and the text often doesn't say which one a record got.
- *How I know:* the two biggest off-diagonal cells in the confusion matrices are HIGH→MEDIUM (55 / 37 / 40) and MEDIUM→HIGH (32 / 26 / 41) for seeds 42 / 7 / 2024. Together they are 87, 63 and 81 posts, which is 51%, 44% and 50% of all errors. Both labels have plenty of data (1,319 MEDIUM, 1,284 HIGH) and both pass criterion 3, so this is not a data-volume problem.
- *Agreement report:* 5 of my 7 disagreements were on this pair (#1, #2, #3, #5, #7). Two were pile (a): I pushed an out-of-bounds read from MEDIUM to HIGH by using knowledge that isn't in the post. Three were pile (b) or (c) with no clear winner under the written rule (#3 was a win for me, #5 and #7 were gaps in the rule). So a careful reader with a written rule also splits on this boundary.

**Diagnosis 2 — Criteria 2, 3, 4 (CRITICAL): HIGH vs CRITICAL is a hard pair that the description doesn't decide.**
- *Cause:* CRITICAL is neither too small nor ignored by the model; it is confused with HIGH in both directions.
- *How I know:* CRITICAL has 455 examples (about 318 in training), far more than LOW. Yet recall is 0.26 / 0.49 / 0.41 and precision is 0.55 / 0.52 / 0.54, so about half of the CRITICAL predictions are wrong and about half of the real CRITICAL posts are missed. Of 68 true CRITICAL test posts, 33 / 28 / 26 (49% / 41% / 38%) were called HIGH, and 13 / 21 / 19 true HIGH posts were called CRITICAL. A label with this much data that stays near 0.4–0.5 F1 points at the boundary, not at the volume.
- *Evidence the text under-determines the label:* my own hard cases 1–3. CVE-2026-5883 and CVE-2026-11068 use the same "execute arbitrary code inside a sandbox" wording as posts whose official severity differs, and "sandbox escape" appears in both HIGH and CRITICAL descriptions. Severity comes from the CVSS vector and score band (7.0–8.9 vs 9.0–10.0), which the description doesn't contain. My dataset also deliberately keeps identical descriptions that carry different official severities, which puts a ceiling on this boundary.
- *Agreement report:* the 2 HIGH/CRITICAL disagreements (#4, the Firefox memory-safety post, and #6, the web midi use-after-free) were not resolved by the written rule (#6 was a rule gap; #4 turned on a hedge in the wording). Neither was a loose application of a clear rule.
- *Instability:* seed 42 in my unit 5 `results.json` had a CRITICAL F1 of 0.057, while the three-seed run gives 0.356 on the same seed and the same test split. So CRITICAL is also sensitive to training setup, which is consistent with a model that hasn't settled on where to put this line.

**Diagnosis 3 — Criteria 2, 3, 4 (LOW): too few examples, and a small test split.**
- *Cause:* LOW is my smallest label by a wide margin.
- *How I know:* 117 examples in total (3.7%), about 82 in training and only 18 in the test split. LOW recall is 3/18, 7/18 and 5/18, and 11 / 8 / 11 of the LOW posts were called MEDIUM. LOW F1 has the biggest seed-to-seed swing in the table (0.231 to 0.467, spread 0.236), and one LOW post changes its recall by 0.056, so a single seed says very little about LOW.
- *Not hopeless:* both of my chosen LOW examples contain a precondition cue ("a remote attacker who had compromised the renderer process"), so some of LOW is learnable from text. That suggests more LOW signal could be recovered with weighting or more data rather than being impossible.
- *Agreement report:* the staff set had no LOW posts, so it tells me nothing about LOW.

**Diagnosis 4 — Criterion 5 (confidence): a measurement gap, not a model failure.**
- *Cause:* my evaluation output reports accuracy by confidence third, not predictions at ≥ 0.90.
- *How I know:* the top-third accuracies (0.868 / 0.931 / 0.893) clear 0.85, and the least confident third is correct only 43% / 57% / 46% of the time, so confidence does rank predictions usefully. But the model is overconfident: mean confidence when right is about 0.83 and when wrong about 0.70–0.74. I cannot say whether the ≥ 0.90 set meets 0.85 until I save each prediction's top probability. I am leaving the criterion as written. It is measurable, I just haven't measured it yet.

**What the agreement report can and can't tell me here.** It can't detect noise in the CVSS-derived labels, because the staff and I both labelled from text. What it does show is that a careful text-only reader using written rules splits on exactly the boundaries where the model confuses most (5 of 7 on MEDIUM/HIGH, 2 of 7 on HIGH/CRITICAL, and 3 of 7 could not be settled by the rules at all). That makes this look more like hard label pairs than a weak model. The two pile (a) misses show a habit of mine (using outside knowledge to push a label up), but it does not touch the training labels, since I didn't write those. Caveat: the staff rubric and staff labels in this check were simulated, and I had already seen the CVSS labels when I labelled the 30 posts, so 77% is not a clean measurement and I use it only as evidence about where text-only rules break down.

**What I haven't tested.** I haven't ruled out truncation (`max_length` 128) as part of the HIGH/CRITICAL problem, and I haven't counted how many identical descriptions carry different severities, which would give a floor on the error that no model could beat. Both checks are cheap and decide whether my next change should target the model (class weights for LOW and CRITICAL, longer inputs) or accept a ceiling set by the labels.



---

## Agreement Report

<!-- Your rate against the staff set, and every disagreement adjudicated.

     Remember you labelled these 30 under the STAFF taxonomy in
     data/staff_taxonomy.md, not your own — so every argument below is made
     from those definitions and those decision rules. -->

**Agreement rate:** 23 / 30 = 77%

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
>“an out-of-bounds read vulnerability exists in the decodelookuptable function within dicomimagedecoder.cpp. the lookup-table decoding logic used for palette color images does not validate pixel…”
> *Staff said / I said:*
>MEDIUM / HIGH
> *My call, and why:*
>Staff is right. The visible text describes an out-of-bounds read and states no disclosure, crash or code execution. Rule 4 says a read with no stated impact is MEDIUM, and rule 5 says to judge only the visible text. I went to HIGH because DICOM parsers handle untrusted files, which is outside knowledge the rules tell me not to use.
> *Which pile:*
> (a) the rule covered it and I applied it loosely

**2.**
> *The post:*
>“an out-of-bounds read vulnerability exists in dicomstreamreader during dicom meta-header parsing. when processing malformed metadata structures, the parser may read beyond the bounds of the…”
> *Staff said / I said:*
>MEDIUM / HIGH
> *My call, and why:*
>Staff is right, for the same reason as #1. This is a read with no stated impact, so rule 4 gives MEDIUM, and the cut-off text can’t be filled in under rule 5. This is the same mistake repeated, which shows it was a habit and not a one-off slip.
> *Which pile:*
> (a) the rule covered it and I applied it loosely

**3.**
> *The post:*
>“insufficient data validation in media in google chrome prior to <version> allowed a remote attacker to perform an out of bounds memory read via a crafted video file.”
> *Staff said / I said:*
>HIGH / MEDIUM
> *My call, and why:*
>I think I’m right. This is an out-of-bounds read with no stated crash, disclosure or code execution, so rule 4 gives MEDIUM. Staff’s own labels agree with that rule: they gave MEDIUM to the two DICOM reads and to the webml read that leaks process memory. HIGH here contradicts rule 4 unless staff treated “remote attacker” as enough on its own, and rule 4 is the more specific rule.
> *Which pile:*
> (c) the rule is ambiguous here and my reading is defensible. This is a win.

**4.**
> *The post:*
>“memory safety bugs present in firefox <version> and thunderbird <version>. some of these bugs showed evidence of memory corruption and we presume that with enough effort some of these could have been…”
> *Staff said / I said:*
>HIGH / CRITICAL
> *My call, and why:*
>I think my reading is more consistent. Staff labelled the near-identical Firefox ESR post CRITICAL. Rule 1 allows CRITICAL for vendor-stated evidence of memory corruption in a core client, and both posts state that. The only visible difference is the hedge “we presume…”, so staff may have read this one as speculative. That reading is not unreasonable, but the hedge is about exploitation, not about the evidence the vendor reports, so I would keep both posts at the same label.
> *Which pile:*
> (c) the rule is ambiguous here and my reading is defensible. This is a win, with the caveat that staff has a real counter-argument.

**5.**
> *The post:*
>“improper access control in the notification management endpoints in devolutions server allows an unauthenticated attacker to modify or delete arbitrary user notification records via missing session…”
> *Staff said / I said:*
>MEDIUM / HIGH
> *My call, and why:*
>The rules don’t settle it. Rule 2 makes unauthenticated tampering with server configuration HIGH, but it says nothing about unauthenticated writes to data records. I extended it by analogy because the access is unauthenticated and covers modify and delete. Staff read notification records as low value. Both readings are defensible, so the definitions need to say whether unauthenticated write access to records counts, and whether the value of the records matters.
> *Which pile:*
> (b) the rule genuinely doesn’t say

**6.**
> *The post:*
>“use after free in web midi in google chrome on android prior to <version> allowed a remote attacker to execute arbitrary code via a crafted html page.”
> *Staff said / I said:*
>CRITICAL / HIGH
> *My call, and why:*
>The rules don’t settle it. Rule 1 needs no user interaction and code execution outside a sandbox. The post doesn’t mention a sandbox, and staff read that silence as outside it. I read “crafted html page” as a victim having to load the page, which is user interaction. The rules don’t define “user interaction” or say what silence about the sandbox implies, so neither of us can be shown wrong.
> *Which pile:*
> (b) the rule genuinely doesn’t say

**7.**
> *The post:*
>“the magic export & import wordpress plugin before <version> stores exported csv files at a publicly accessible location, making it possible for any visitors to leak sensitive user information.”
> *Staff said / I said:*
>HIGH / MEDIUM
> *My call, and why:*
>The rules don’t settle it. Rule 3 makes an info leak MEDIUM when its scope is “bounded”, but never defines bounded. The post is an unauthenticated leak of sensitive user information, which pulls toward HIGH, but it is still an info leak, and rule 2 lists none as HIGH. I weighted the type of impact and staff weighted the lack of authentication. The definitions need to say whether unauthenticated access to bulk user data lifts a leak above MEDIUM.
> *Which pile:*
> (b) the rule genuinely doesn’t say


**What the pattern in my disagreements tells me:**
The 7 disagreements split into 2 in pile (a), 2 in pile (c) and 3 in pile (b).

Pile (a): both misses are the same error, where I used knowledge from outside the post (that DICOM parsers handle untrusted files) to push an out-of-bounds read up a level. Rule 4 and rule 5 forbid exactly that. Across my own 200 labels, the risk is that I let product familiarity or my sense of how bad a bug usually is override what the text actually says. I should re-check my 200 for places where a label depends on something that isn’t in the text.
Pile (c): both wins come from consistency. In #3 staff broke its own rule 4 pattern, and in #4 the same vendor-stated evidence got two different labels. That tells me I apply a rule the same way when two posts match, and that will matter when I check my 200 for internal consistency.
Pile (b): three of the seven disagreements trace to undefined terms: “user interaction”, “bounded”, and unauthenticated writes to data. Those are definition problems and not labelling problems, so they are the first things to tighten in my own taxonomy before I blame the labels or the model.
Overall: most of the disagreement sits on the MEDIUM/HIGH boundary. If a model struggles there in Milestone 4, I should first check whether the boundary is poorly defined before concluding the model is weak.


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
