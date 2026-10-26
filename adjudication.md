# Adjudication — 7 disagreements (agreement 23/30 = 77%)

Caveat: the staff set is synthetic and my labels were not blind (I had seen the CVSS labels). The reasoning below argues only from `data/staff_taxonomy.md`.

| # | Post (start) | Staff | Me | Pile |
|---|---|---|---|---|
| 1 | dicom `decodelookuptable` OOB read | MEDIUM | HIGH | (a) |
| 28 | dicom `dicomstreamreader` OOB read | MEDIUM | HIGH | (a) |
| 12 | chrome media OOB read, crafted video | HIGH | MEDIUM | (c) |
| 7 | firefox/thunderbird memory safety | HIGH | CRITICAL | (c) |
| 2 | devolutions unauthenticated notification edits | MEDIUM | HIGH | (b) |
| 15 | chrome web midi UAF, code exec | CRITICAL | HIGH | (b) |
| 18 | magic export & import public CSVs | HIGH | MEDIUM | (b) |

## (a) Rule covered it, I applied it loosely
**#1 and #28 — staff MEDIUM, I said HIGH.** Both posts describe an out-of-bounds read with no stated disclosure, crash or code execution in the visible text. Rule 4 says that is MEDIUM, and rule 5 says to judge only what is visible. I labelled them HIGH because DICOM parsers handle untrusted files, which is outside knowledge that the rules tell me not to use. Staff is right on both. I was also consistent with myself across the two, so this is one error repeated, not two.

## (c) Ambiguous, and my reading is defensible
**#12 — staff HIGH, I said MEDIUM.** The post is an out-of-bounds read triggered by a crafted video file, with no crash or code execution stated. Rule 4 puts that at MEDIUM. Staff's own labels support this: they gave MEDIUM to #1 and #28 (reads) and MEDIUM to #21 (a read leaking process memory). HIGH here contradicts rule 4 and staff's own pattern, unless staff treated "remote attacker" as the trigger for HIGH. Rule 4 is more specific than that, so I think I'm right and staff was inconsistent.

**#7 — staff HIGH, I said CRITICAL.** This is near-identical to #4, which staff labelled CRITICAL. Both say some bugs showed evidence of memory corruption. The only visible difference is that #7 includes "we presume … could have been", so staff may have read it as speculative. Rule 1 says CRITICAL covers "vendor-stated evidence of memory corruption in a core client". That is stated in both posts, so the same label should apply to both. The hedge doesn't change what the vendor states about evidence. I think my reading is more consistent, but staff's hedging argument is not unreasonable.

## (b) The rule doesn't say
**#2 — staff MEDIUM, I said HIGH.** Rule 2 makes unauthenticated tampering with server *configuration* HIGH, but says nothing about unauthenticated modification or deletion of *data records* such as notifications. I extended the rule by analogy, and staff treated notifications as low-value. Gap: the rules should say whether unauthenticated write access to records counts, and whether the value of the records matters.

**#15 — staff CRITICAL, I said HIGH.** Rule 1 requires "no user interaction" and "code execution outside a sandbox". The post gives remote code execution via a crafted HTML page and doesn't mention a sandbox. Staff read the absence of "inside a sandbox" as outside it. I read "crafted HTML page" as needing a visit, so user interaction. The rules don't say whether loading a page counts as interaction, and rule 5 doesn't say what to do when a sandbox is simply not mentioned. Gap: define "user interaction" and what silence about the sandbox implies.

**#18 — staff HIGH, I said MEDIUM.** Rule 3 makes an info leak MEDIUM when its scope is "bounded", but never defines bounded. This post says any visitor can leak "sensitive user information" from a public CSV. That is unauthenticated, but the exact data and scale aren't visible. Staff weighted the unauthenticated access, and I weighted the fact that it is an information leak. Gap: define "bounded", and say whether unauthenticated access to bulk user data lifts a leak to HIGH.

## Takeaways
- Two of the 7 were my own loose application (pile a), and the pattern was importing outside knowledge, which rule 5 forbids.
- Three of the 7 point to missing definitions: "user interaction", "bounded", and unauthenticated writes to data. These are the first places to tighten the rules.
- Staff #12 vs #1/#28/#21 is the one place where a careful reader should *win* the argument.
