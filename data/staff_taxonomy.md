# The staff set — severity taxonomy and rules (synthetic)

Labels follow `label_definitions.txt`. Judge the **visible text only**; do not look up the CVE.

**LOW** — limited impact or needs unusual conditions (local access, rare config). Reserved; may not appear in this set.
**MEDIUM** — bounded impact: information leak, spoofing, policy/CSP bypass, XSS, or anything needing a user gesture or precondition.
**HIGH** — serious impact: remote memory corruption or code execution confined to a sandbox, unauthenticated server DoS, unauthenticated configuration tampering, privilege escalation.
**CRITICAL** — remote, no authentication, no user interaction, and the text states full compromise: code execution outside a sandbox, authentication/crypto bypass, or vendor-stated evidence of memory corruption in a core client.

## Decision rules
1. **CRITICAL vs HIGH** — CRITICAL needs remote + no auth + no user interaction + full compromise. If any is missing, HIGH.
2. **HIGH vs MEDIUM** — unauthenticated tampering with server configuration, privilege escalation, or sandboxed code execution is HIGH. Info leaks and bypasses are MEDIUM.
3. **Info leaks** — a leak is MEDIUM when its scope is bounded (a single origin, process memory, a URL bar).
4. **Out-of-bounds reads** — a read with no stated disclosure, crash or code execution is MEDIUM. With a stated crash it is HIGH.
5. **Truncated text** — judge what is visible. Do not guess what the cut-off part says.
6. **Tie-break** — when two labels are still defensible, pick the lower one. Use only after rules 1–5.
