#!/usr/bin/env python3
"""Extract CVSS-severity labels from a directory of CVE JSON records."""

import argparse
import csv
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "data" / "CVE_2026"
DEFAULT_OUTPUT_CSV = ROOT / "labels.csv"

LABEL_MAP = {
    "LOW": "LOW",
    "MEDIUM": "MEDIUM",
    "HIGH": "HIGH",
    "CRITICAL": "CRITICAL",
}

MAX_TEXT_LENGTH = 200
CVSS_KEYS = ("cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0")
SKIP_REASONS = (
    "no_description",
    "no_severity",
    "unknown_severity",
    "too_short",
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


def extract_records(input_dir: Path) -> tuple[list[dict[str, str]], Counter[str]]:
    rows: list[dict[str, str]] = []
    stats: Counter[str] = Counter()
    seen_text_severity: set[tuple[str, str]] = set()

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

            description = extract_description(data)
            if not description:
                stats["no_description"] += 1
                continue

            severity = extract_severity(data)
            if not severity:
                stats["no_severity"] += 1
                continue
            if severity not in LABEL_MAP:
                stats["unknown_severity"] += 1
                continue

            text = clean_text(description)
            if not text or len(text) < 20:
                stats["too_short"] += 1
                continue

            # Keep identical text with distinct official severities: discarding one
            # would silently choose a label. Only exact text-and-label repeats drop.
            dedup_key = (text, severity)
            if dedup_key in seen_text_severity:
                stats["duplicate"] += 1
                continue
            seen_text_severity.add(dedup_key)

            rows.append({
                "text": text,
                "label": LABEL_MAP[severity],
                "note": extract_cve(data),
            })
            stats[f"label_{severity}"] += 1

    stats["records_extracted"] = len(rows)
    return rows, stats


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["text", "label", "note"],
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"directory of CVE JSON files (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
        help=f"output CSV path (default: {DEFAULT_OUTPUT_CSV})",
    )
    args = parser.parse_args()
    if not args.input_dir.is_dir():
        parser.error(f"input directory does not exist: {args.input_dir}")

    rows, stats = extract_records(args.input_dir)
    write_csv(rows, args.output)

    print()
    print("=" * 60)
    print(f"JSON files scanned : {stats['json_files_scanned']}")
    print(f"Records extracted  : {stats['records_extracted']}")
    print(f"Read errors        : {stats['read_errors']}")
    print("Skip reasons:")
    for reason in SKIP_REASONS:
        print(f"  {reason.replace('_', ' '):<20}: {stats[reason]}")
    print()
    print("Class distribution:")
    for label in LABEL_MAP:
        print(f"  {label:<8}: {stats[f'label_{label}']}")
    print()
    print(f"Saved: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
