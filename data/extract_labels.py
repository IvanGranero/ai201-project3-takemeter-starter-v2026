import os
import csv
import json
import re
from collections import Counter

INPUT_DIR = r"./data/CVE_2026"
OUTPUT_CSV = "labels.csv"

LABEL_MAP = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}

MAX_TEXT_LENGTH = 200


def clean_text(text: str) -> str:
    if not text:
        return None

    # Collapse whitespace/newlines/tabs
    text = re.sub(r"\s+", " ", text)

    # Remove Chromium severity suffix
    text = re.sub(
        r"\(chromium security severity:.*?\)",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Replace version numbers
    text = re.sub(
        r"\b\d+\.\d+(?:\.\d+)*\b",
        "<VERSION>",
        text
    )

    text = text.strip().lower()

    # Truncate to 200 characters, preserving words
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
        text = text.rsplit(" ", 1)[0]

    return text


def extract_severity(data):
    try:
        metrics = data["containers"]["adp"][0]["metrics"]

        for metric in metrics:
            cvss = metric.get("cvssV3_1")
            if cvss:
                severity = cvss.get("baseSeverity")
                if severity:
                    return severity.upper()

    except Exception:
        pass

    return None


def extract_description(data):
    try:
        return data["containers"]["cna"]["descriptions"][0]["value"]
    except Exception:
        return None


def extract_cve(data):
    try:
        return data["cveMetadata"]["cveId"]
    except Exception:
        return "UNKNOWN"


rows = []
seen_texts = set()
label_counter = Counter()

json_count = 0
skipped = 0

for root, dirs, files in os.walk(INPUT_DIR):
    for filename in files:

        if not filename.lower().endswith(".json"):
            continue

        filepath = os.path.join(root, filename)
        json_count += 1

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            text = extract_description(data)
            severity = extract_severity(data)

            if not text or not severity:
                skipped += 1
                continue

            text = clean_text(text)

            if not text:
                skipped += 1
                continue

            # Skip tiny descriptions
            if len(text) < 20:
                skipped += 1
                continue

            # Deduplicate
            text_hash = (text, severity)

            if text_hash in seen_texts:
                continue

            seen_texts.add(text_hash)

            if severity not in LABEL_MAP:
                skipped += 1
                continue

            label = LABEL_MAP[severity]
            cve_id = extract_cve(data)

            rows.append({
                "text": text,
                "label": label,
                "note": cve_id
            })

            label_counter[severity] += 1

        except Exception as e:
            print(f"[ERROR] {filepath}")
            print(f"        {e}")
            skipped += 1

with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["text", "label", "note"],
        quoting=csv.QUOTE_MINIMAL
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

print()
print("=" * 60)
print(f"JSON files scanned : {json_count}")
print(f"Records extracted  : {len(rows)}")
print(f"Skipped            : {skipped}")
print()
print("Class distribution:")
for label, count in sorted(label_counter.items()):
    print(f"  {label:<8} : {count}")
print()
print(f"Saved: {OUTPUT_CSV}")
print("=" * 60)