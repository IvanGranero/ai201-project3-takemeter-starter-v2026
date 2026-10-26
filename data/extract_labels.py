#!/usr/bin/env python3
"""Extract CVSS-severity labels from CVE records.

Two input layouts are supported (see SOURCE_FORMAT below):
  "nvd"  - an NVD API 2.0 feed: one big JSON with a "vulnerabilities" list (2025 data)
  "cve5" - a folder of individual CVE JSON 5 records (the 2026 data behind labels.csv)
"""

import argparse
import csv
import json
import os
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]

# ── INPUT / OUTPUT / FORMAT ──────────────────────────────────────────────────
# 2026 run — this is what produced labels.csv. Kept for reference; to rebuild
# labels.csv, uncomment these three lines and comment out the 2025 block below.
# DEFAULT_INPUT = ROOT / "data" / "CVE_2026"          # folder of CVE JSON 5 files
# DEFAULT_OUTPUT_CSV = ROOT / "labels.csv"
# SOURCE_FORMAT = "cve5"

# 2025 run — extra training rows. Writes extra.csv, NEVER labels.csv.
# DEFAULT_INPUT can be the feed file itself or a folder of feed files; or pass
# --input path/to/file.json on the command line.
DEFAULT_INPUT = ROOT / "data" / "CVE_2025"
DEFAULT_OUTPUT_CSV = ROOT / "extra.csv"
SOURCE_FORMAT = "nvd"

# Descriptions already in this file are skipped, so extra.csv can't repeat or
# contradict a row the test split was drawn from. Set to None to turn off.
DEFAULT_EXCLUDE_CSV = ROOT / "labels.csv"

# ── LABEL FILTER ─────────────────────────────────────────────────────────────
# Which severities to keep.
#   LOW and CRITICAL only (current):   KEEP_LABELS = {"LOW", "CRITICAL"}
#   LOW only (the graded improvement): KEEP_LABELS = {"LOW"}
#   CRITICAL only:                     KEEP_LABELS = {"CRITICAL"}
#   EVERYTHING (all four labels):      KEEP_LABELS = None
# To extract everything, comment out the active line and uncomment the None line.
KEEP_LABELS = {"LOW", "CRITICAL"}
# KEEP_LABELS = None

# ── WHICH SCORE BECOMES THE LABEL (nvd format only) ──────────────────────────
# One CVE can carry several scores, and they disagree. In your own sample,
# CVE-2025-0175 is LOW by the CNA (vuldb) but MEDIUM by NVD, and CVE-2025-0168
# is MEDIUM by the CNA but HIGH by NVD. Whichever source you pick decides the
# label, and whether a row is LOW at all. Pick the one that matches how the
# 2026 labels were made, and keep it the same for every row.
SEVERITY_SOURCE = "cisa_adp"   # best guess at the 2026 rule ("first ADP entry"); verify it
# SEVERITY_SOURCE = "nvd"      # NVD's own Primary score (nvd@nist.gov)
# SEVERITY_SOURCE = "cna"      # the score from the CVE's own CNA (e.g. cna@vuldb.com)
# SEVERITY_SOURCE = "any"      # first score found, from whoever — mixes rules, not advised

CISA_ADP_ID = "134c704f-9b21-4f2e-91b3-4a467353bcc0"   # CISA-ADP, as in the ssvc entries
NVD_SOURCE = "nvd@nist.gov"

LABEL_MAP = {
    "LOW": "LOW",
    "MEDIUM": "MEDIUM",
    "HIGH": "HIGH",
    "CRITICAL": "CRITICAL",
}

MAX_TEXT_LENGTH = 200
CVSS_KEYS = ("cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0")                 # cve5 layout
NVD_METRIC_KEYS = ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2")  # nvd layout
SKIP_REASONS = (
    "no_description",
    "no_severity",
    "unknown_severity",
    "filtered_out",
    "too_short",
    "already_in_labels_csv",
    "duplicate",
)


def clean_text(text: str | None) -> str | None:
    if not text:
        return None

    text = re.sub(r"\s+", " ", text)
    text = re.sub(
        r"\(chromium security severity:.*?\)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b\d+\.\d+(?:\.\d+)*\b", "<VERSION>", text)
    text = text.strip().lower()

    # Keep the original corpus' 200-character cap for consistent model inputs;
    # this bounds noisy descriptions but can discard a distinguishing clause.
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH].rsplit(" ", 1)[0]

    return text


def add_row(
    rows: list[dict[str, str]],
    stats: Counter[str],
    seen: set[tuple[str, str]],
    exclude_texts: set[str],
    severity: str | None,
    description: str | None,
    cve_id: str,
    source: str,
) -> None:
    """Shared by both layouts: validate, filter, clean, de-duplicate, keep."""
    if not description:
        stats["no_description"] += 1
        return
    if not severity:
        stats["no_severity"] += 1
        return
    if severity not in LABEL_MAP:
        stats["unknown_severity"] += 1
        return

    # ── LABEL FILTER (applies KEEP_LABELS from the top of the file) ──────────
    # Drops every severity not in KEEP_LABELS (currently: keeps only LOW and
    # CRITICAL). To extract everything, set KEEP_LABELS = None at the top, or
    # comment out these three lines.
    if KEEP_LABELS is not None and severity not in KEEP_LABELS:
        stats["filtered_out"] += 1
        return

    text = clean_text(description)
    if not text or len(text) < 20:
        stats["too_short"] += 1
        return

    # Skip anything already in labels.csv (same text, any label).
    if text in exclude_texts:
        stats["already_in_labels_csv"] += 1
        return

    # Keep identical text with distinct official severities: discarding one
    # would silently choose a label. Only exact text-and-label repeats drop.
    key = (text, severity)
    if key in seen:
        stats["duplicate"] += 1
        return
    seen.add(key)

    rows.append({"text": text, "label": LABEL_MAP[severity], "note": cve_id, "_source": source})
    stats[f"label_{severity}"] += 1


# ═════════════════════ nvd layout (2025 feed) ════════════════════════════════

def iter_vulnerabilities(path: Path, chunk_size: int = 4 << 20) -> Iterator[dict[str, Any]]:
    """Stream the items of "vulnerabilities" one at a time.

    The feed is hundreds of MB; json.load would hold all of it in memory. A
    record cut off at end-of-file (a truncated download) raises JSONDecodeError
    after every complete record before it has been yielded.
    """
    decoder = json.JSONDecoder()
    marker = '"vulnerabilities"'
    with path.open("r", encoding="utf-8") as file:
        buf = ""
        while True:  # find the opening [ of the list
            chunk = file.read(chunk_size)
            if not chunk:
                raise ValueError(f'no "vulnerabilities" list found in {path}')
            buf += chunk
            i = buf.find(marker)
            if i == -1:
                buf = buf[-len(marker):]
                continue
            j = buf.find("[", i)
            if j == -1:
                buf = buf[i:]
                continue
            buf = buf[j + 1:]
            break

        while True:
            buf = buf.lstrip()
            while buf[:1] == ",":
                buf = buf[1:].lstrip()
            if buf[:1] == "]":
                return
            if not buf:
                chunk = file.read(chunk_size)
                if not chunk:
                    return
                buf = chunk
                continue
            try:
                item, end = decoder.raw_decode(buf)
            except json.JSONDecodeError:
                chunk = file.read(chunk_size)
                if not chunk:
                    raise
                buf += chunk
                continue
            yield item
            buf = buf[end:]


def metric_allowed(metric: dict[str, Any], cve: dict[str, Any]) -> bool:
    """Does this score come from the source SEVERITY_SOURCE asks for?"""
    source = metric.get("source")
    if SEVERITY_SOURCE == "cisa_adp":
        return source == CISA_ADP_ID
    if SEVERITY_SOURCE == "nvd":
        return source == NVD_SOURCE
    if SEVERITY_SOURCE == "cna":
        return source == cve.get("sourceIdentifier")
    return True  # "any"


def extract_severity_nvd(cve: dict[str, Any]) -> str | None:
    """First usable baseSeverity, newest CVSS version first (same order as 2026)."""
    metrics = cve.get("metrics")
    if not isinstance(metrics, dict):
        return None
    for key in NVD_METRIC_KEYS:
        entries = metrics.get(key)
        if not isinstance(entries, list):
            continue
        for metric in entries:
            if not isinstance(metric, dict) or not metric_allowed(metric, cve):
                continue
            cvss = metric.get("cvssData")
            severity = cvss.get("baseSeverity") if isinstance(cvss, dict) else None
            if not severity:                       # CVSS v2 keeps it on the metric itself
                severity = metric.get("baseSeverity")
            if isinstance(severity, str) and severity.strip():
                return severity.strip().upper()
    return None


def extract_description_nvd(cve: dict[str, Any]) -> str | None:
    descriptions = cve.get("descriptions")
    if not isinstance(descriptions, list):
        return None
    for item in descriptions:                      # prefer English
        if isinstance(item, dict) and item.get("lang") == "en" and isinstance(item.get("value"), str):
            return item["value"]
    for item in descriptions:
        if isinstance(item, dict) and isinstance(item.get("value"), str):
            return item["value"]
    return None


def input_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".json")


def extract_records_nvd(
    input_path: Path, exclude_texts: set[str]
) -> tuple[list[dict[str, str]], Counter[str]]:
    rows: list[dict[str, str]] = []
    stats: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()

    for filepath in input_files(input_path):
        stats["json_files_scanned"] += 1
        try:
            for item in iter_vulnerabilities(filepath):
                stats["records_scanned"] += 1
                cve = item.get("cve") if isinstance(item, dict) else None
                if not isinstance(cve, dict):
                    stats["read_errors"] += 1
                    continue
                add_row(
                    rows, stats, seen, exclude_texts,
                    extract_severity_nvd(cve),
                    extract_description_nvd(cve),
                    str(cve.get("id") or "UNKNOWN"),
                    str(cve.get("sourceIdentifier") or "UNKNOWN"),
                )
        except (OSError, UnicodeDecodeError, ValueError) as error:  # JSONDecodeError is a ValueError
            stats["read_errors"] += 1
            print(f"[ERROR] {filepath}: {error}")
            print("        Records before the error were kept.")

    stats["records_extracted"] = len(rows)
    return rows, stats


# ═════════════════════ cve5 layout (2026 records) ════════════════════════════

def extract_severity(data: dict[str, Any]) -> str | None:
    """Return the first available CVSS base severity, preferring newer formats."""
    containers = data.get("containers")
    if not isinstance(containers, dict):
        return None

    adp = containers.get("adp")
    # Retain the first-ADP source policy used to create labels.csv; only the
    # CVSS version lookup expands to cover newer and older schema keys.
    if not isinstance(adp, list) or not adp or not isinstance(adp[0], dict):
        return None
    metrics = adp[0].get("metrics")
    if not isinstance(metrics, list):
        return None

    for key in CVSS_KEYS:
        for metric in metrics:
            if isinstance(metric, dict):
                cvss = metric.get(key)
                if isinstance(cvss, dict):
                    severity = cvss.get("baseSeverity")
                    if isinstance(severity, str) and severity.strip():
                        return severity.strip().upper()

    return None


def extract_description(data: dict[str, Any]) -> str | None:
    containers = data.get("containers")
    if not isinstance(containers, dict):
        return None
    cna = containers.get("cna")
    if not isinstance(cna, dict):
        return None
    descriptions = cna.get("descriptions")
    if not isinstance(descriptions, list):
        return None
    if not descriptions or not isinstance(descriptions[0], dict):
        return None
    value = descriptions[0].get("value")
    return value if isinstance(value, str) else None


def extract_cve(data: dict[str, Any]) -> str:
    metadata = data.get("cveMetadata")
    if isinstance(metadata, dict):
        cve_id = metadata.get("cveId")
        if isinstance(cve_id, str) and cve_id.strip():
            return cve_id.strip()
    return "UNKNOWN"


def extract_source_cve5(data: dict[str, Any]) -> str:
    try:
        return str(data["containers"]["cna"]["providerMetadata"]["shortName"])
    except (KeyError, TypeError):
        return "UNKNOWN"


def extract_records_cve5(
    input_dir: Path, exclude_texts: set[str]
) -> tuple[list[dict[str, str]], Counter[str]]:
    rows: list[dict[str, str]] = []
    stats: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()

    def report_walk_error(error: OSError) -> None:
        stats["read_errors"] += 1
        print(f"[ERROR] {error.filename}: {error}")

    for root, _directories, filenames in os.walk(input_dir, onerror=report_walk_error):
        for filename in filenames:
            if not filename.lower().endswith(".json"):
                continue
            filepath = Path(root) / filename
            stats["json_files_scanned"] += 1
            try:
                with filepath.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                stats["read_errors"] += 1
                print(f"[ERROR] {filepath}: {error}")
                continue

            if not isinstance(data, dict):
                stats["read_errors"] += 1
                print(f"[ERROR] {filepath}: expected a JSON object at the document root")
                continue

            stats["records_scanned"] += 1
            add_row(
                rows, stats, seen, exclude_texts,
                extract_severity(data),
                extract_description(data),
                extract_cve(data),
                extract_source_cve5(data),
            )

    stats["records_extracted"] = len(rows)
    return rows, stats


# ═════════════════════ shared ════════════════════════════════════════════════

def load_exclude_texts(path: Path | None) -> set[str]:
    """Descriptions already present in an existing labels file."""
    if path is None or not path.is_file():
        return set()
    with path.open("r", encoding="utf-8", newline="") as file:
        return {row["text"] for row in csv.DictReader(file) if row.get("text")}


def sample_rows(
    rows: list[dict[str, str]], n: int, max_per_source: int | None, seed: int
) -> list[dict[str, str]]:
    """A reproducible random sample of up to n rows per label.

    max_per_source caps how many rows may come from one source (e.g. one CNA),
    so a single vendor's boilerplate can't fill the whole sample.
    """
    rng = random.Random(seed)
    ordered = sorted(rows, key=lambda r: (r["note"], r["text"]))  # stable before shuffling
    chosen: list[dict[str, str]] = []
    for label in LABEL_MAP:
        group = [r for r in ordered if r["label"] == label]
        rng.shuffle(group)
        picked: list[dict[str, str]] = []
        per_source: Counter[str] = Counter()
        for row in group:
            if max_per_source and per_source[row["_source"]] >= max_per_source:
                continue
            picked.append(row)
            per_source[row["_source"]] += 1
            if len(picked) == n:
                break
        chosen.extend(sorted(picked, key=lambda r: r["note"]))
    return chosen


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["text", "label", "note"],
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",          # drops the internal _source field
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", "--input-dir", dest="input", type=Path, default=DEFAULT_INPUT,
                        help=f"feed file, or folder of JSON files (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV,
                        help=f"output CSV path (default: {DEFAULT_OUTPUT_CSV})")
    parser.add_argument("--format", choices=("nvd", "cve5"), default=SOURCE_FORMAT,
                        help=f"input layout (default: {SOURCE_FORMAT})")
    parser.add_argument("--exclude", type=Path, default=DEFAULT_EXCLUDE_CSV,
                        help="skip descriptions already in this CSV (default: labels.csv if it exists)")
    parser.add_argument("--sample-per-label", type=int, default=None, metavar="N",
                        help="keep a random sample of N rows per label (e.g. 30). Default: keep all.")
    parser.add_argument("--max-per-source", type=int, default=None, metavar="K",
                        help="with sampling, take at most K rows from any one source (e.g. 10)")
    parser.add_argument("--seed", type=int, default=0, help="seed for sampling (default: 0)")
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"input does not exist: {args.input}")

    exclude = load_exclude_texts(args.exclude)
    if args.format == "nvd":
        rows, stats = extract_records_nvd(args.input, exclude)
    else:
        if not args.input.is_dir():
            parser.error("--format cve5 needs a folder of CVE JSON files")
        rows, stats = extract_records_cve5(args.input, exclude)

    found = Counter(r["label"] for r in rows)
    sources: dict[str, Counter[str]] = {label: Counter() for label in LABEL_MAP}
    for r in rows:
        sources[r["label"]][r["_source"]] += 1

    if args.sample_per_label or args.max_per_source:
        rows = sample_rows(rows, args.sample_per_label or 10**9, args.max_per_source, args.seed)
    write_csv(rows, args.output)
    written = Counter(r["label"] for r in rows)

    print()
    print("=" * 60)
    if args.format == "nvd":
        print(f"Severity source    : {SEVERITY_SOURCE}")
    print(f"JSON files scanned : {stats['json_files_scanned']}")
    print(f"CVE records scanned: {stats['records_scanned']}")
    print(f"Records extracted  : {stats['records_extracted']}")
    print(f"Read errors        : {stats['read_errors']}")
    print("Skip reasons:")
    for reason in SKIP_REASONS:
        print(f"  {reason.replace('_', ' '):<22}: {stats[reason]}")
    print()
    print("Class distribution (found -> written):")
    for label in LABEL_MAP:
        print(f"  {label:<8}: {found[label]} -> {written[label]}")
    print()
    print("Biggest sources among the rows found (watch for one source dominating):")
    for label in LABEL_MAP:
        if found[label]:
            top = ", ".join(f"{s} {c}" for s, c in sources[label].most_common(3))
            print(f"  {label:<8}: {top}")
    if args.sample_per_label:
        for label in (KEEP_LABELS or LABEL_MAP):
            if written[label] < args.sample_per_label:
                print(f"  [note] only {written[label]} {label} rows after caps, "
                      f"fewer than the {args.sample_per_label} requested")
    print()
    print(f"Saved: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
