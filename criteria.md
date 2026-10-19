# Acceptance criteria — TakeMeter

Five criteria that say what "working" means for this classifier, written in
unit 5 **before** anything was trained.

**All five are yours this time.** None are given. You've had two projects of
practice.

An acceptance criterion names a number. *"The model is accurate"* is an
opinion. *"Every label has an F1 of at least 0.60 on the held-out set"* is a
criterion.

Under each, write a sentence or two on **why that number**. A reason that says
something about your data or your taxonomy earns credit — *"I picked 0.60 F1
for `reaction` because it's my smallest label and I only have about 50
examples of it"*. A reason that could be attached to any project does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

Not numbers that sound impressive. Three labels means a coin-flip guesser gets
about 33%, so a target of 0.40 is barely a target. Your number should sit
somewhere you'd honestly call useful.

**Cover at least three of these five areas.** They're here as prompts, not as a
form to fill in — a criterion that fits none of them is fine if it names a
number.

| Area | A question it could answer |
|---|---|
| Overall accuracy | How often does it need to be right to be worth using? |
| Per-label performance | Is one label allowed to be much worse than the others? |
| Balance | How lopsided can your label counts get before it's a problem? |
| Consistency | If someone else labelled the same posts, how often should you agree? |
| Confidence | Should a confident prediction be right more often than an unsure one? |

Two things worth knowing before you pick numbers, because both will affect
whether you hit them:

- **Your smallest label will have the jumpiest score.** If a label has 50
  examples, about 8 land in the test split. An F1 computed on 8 examples moves
  a lot between seeds. A target for that label should be looser than one for
  your biggest label, and saying so is a good reason.
- **Unit 6 tests across three seeds, and the target has to hold across all
  three.** A target of 0.65 against results of 0.71, 0.62, 0.68 is a **miss**.
  Pick with that in mind — it is stricter than it first sounds.

---

## 1.

<!-- Your criterion. It must name a number. -->
The model must achieve at least 75% overall accuracy on the held-out test set across all three random seeds.

**Why this target:**
This is a four-class classification problem (LOW, MEDIUM, HIGH, CRITICAL), so random guessing would achieve roughly 25% accuracy. The dataset contains over 3,000 labeled CVE records, which is large enough for DistilBERT to substantially outperform chance. A target of 75% represents a useful classifier while remaining realistic given that many vulnerability descriptions use similar language across severity levels.

---

## 2.

<!-- Your criterion. -->
The macro F1-score must be at least 0.70 on the held-out test set across all three random seeds.

**Why this target:**
Accuracy alone can hide poor performance on minority classes. Macro F1 treats all labels equally, including LOW and CRITICAL. Because LOW represents only 117 samples while MEDIUM and HIGH together account for most of the dataset, macro F1 is necessary to ensure the model performs reasonably across all classes instead of focusing on majority labels.

---

## 3.

<!-- Your criterion. -->
Each label must achieve an F1-score of at least 0.55.

**Why this target:**
The LOW class contains only 117 examples (approximately 3.7% of the dataset), making it difficult to learn compared with MEDIUM and HIGH. Requiring every class to reach 0.70 F1 would be unrealistic, but allowing any class to fall below 0.55 would indicate the classifier is largely failing to recognize that category.

---

## 4.

<!-- Your criterion. -->
The difference between the best-performing label F1-score and the worst-performing label F1-score must not exceed 0.25.

**Why this target:**
The dataset is imbalanced, but the classifier should still provide consistent value across all severity levels. For example, if HIGH achieved 0.90 F1 while LOW achieved 0.40 F1, the model would be unreliable for some severity categories. Limiting the performance gap helps ensure balanced behavior.

---

## 5.

<!-- Your criterion. -->
Predictions with a confidence score of 90% or greater must be correct at least 85% of the time.

**Why this target:**
Security analysts are more likely to trust predictions that the model considers highly confident. If a prediction is reported with very high confidence, it should be correct most of the time. This criterion evaluates calibration rather than raw classification performance and ensures the confidence score remains meaningful.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 6 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Every label performs acceptably

         The model performs well on all labels.

         **Why this target:** ...

         > **Revised in unit 6:** Every label has an F1 of at least 0.60 on
         > the held-out set.
         >
         > **Why revised:** "performs well" gave me nothing to check. I
         > couldn't produce a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "Overall accuracy of at least 0.65" → "at least 0.55", because
            0.65 turned out to be optimistic for 200 examples.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
