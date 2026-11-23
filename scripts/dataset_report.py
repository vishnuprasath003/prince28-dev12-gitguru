"""Measure the GitGuru corpus and generate dataset and capacity reports."""

import argparse
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifest.jsonl"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def read_text(path):
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, len(reader.pages)

        raw = path.read_text(encoding="utf-8", errors="ignore")
        if suffix in {".html", ".htm"}:
            parser = TextExtractor()
            parser.feed(raw)
            raw = " ".join(parser.parts)
        return raw, 1
    except (OSError, ValueError, PdfReadError):
        return "", 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-pages", type=int, default=2000)
    parser.add_argument("--full-files", type=int)
    parser.add_argument("--embed-usd", type=float, default=0.20)
    parser.add_argument("--dims", type=int, default=1024)
    parser.add_argument("--chunk-tokens", type=int, default=500)
    parser.add_argument("--usd-inr", type=float, default=95)
    args = parser.parse_args()

    records = []
    with MANIFEST.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                item = json.loads(line)
                if item.get("status") == "downloaded":
                    records.append(item)

    totals = defaultdict(lambda: {"files": 0, "pages": 0, "bytes": 0, "tokens": 0})
    total_pages = total_tokens = total_bytes = 0
    licence_rows = set()

    for item in records:
        path = ROOT / item["path"]
        if not path.is_file():
            continue

        content, pages = read_text(path)
        tokens = len(re.findall(r"\b[\w'-]+\b", content))
        source = item.get("source", "unknown")
        licence = item.get("licence", "Not specified")

        totals[source]["files"] += 1
        totals[source]["pages"] += pages
        totals[source]["bytes"] += path.stat().st_size
        totals[source]["tokens"] += tokens
        total_pages += pages
        total_tokens += tokens
        total_bytes += path.stat().st_size
        licence_rows.add((source, licence))

    if total_pages == 0:
        raise SystemExit("No readable corpus pages found in the manifest.")

    target_pages = args.full_pages
    if args.full_files:
        target_pages = args.full_files

    tokens_per_page = total_tokens / total_pages
    full_tokens = tokens_per_page * target_pages
    chunks = max(1, int((full_tokens + args.chunk_tokens - 1) // args.chunk_tokens))
    embed_cost = (full_tokens / 1_000_000) * args.embed_usd * args.usd_inr
    vector_mb = chunks * args.dims * 4 / (1024 * 1024)
    text_mb = total_bytes / (1024 * 1024)
    projected_text_mb = text_mb * target_pages / total_pages

    dataset = [
        "# Dataset: GitGuru",
        "",
        "A Git expert that answers from the official Git reference and the Pro Git book, and proves every command in a throwaway repository before showing it.",
        "",
        "- **Start target:** Reference pages for the 40 most-used commands + Pro Git chapters 1-3 and 7",
        "- **Full target:** All reference pages, the full Pro Git book and release notes from 2.30 onwards (2,000+ pages)",
        "- **Collected by:** `scripts/fetch.py` as `examate-student-bot`.",
        "",
        "## Where the documents come from",
        "",
        "- https://git-scm.com/docs",
        "- https://github.com/git/git (Documentation/)",
        "- https://github.com/progit/progit2",
        "",
        "## Terms I follow",
        "",
        "Git docs GPL-2.0 with the code; Pro Git CC BY-NC-SA 3.0 (non-commercial, attribute).",
        "",
        "- Every answer links to the original document.",
        "- No personal data is collected.",
        "",
        "<!-- generated:start -->",
        "",
        "| Source | Files | Pages | Size (MB) | Tokens | Licence |",
        "|---|---:|---:|---:|---:|---|",
    ]

    for source, data in sorted(totals.items()):
        licences = sorted({lic for src, lic in licence_rows if src == source})
        dataset.append(
            f"| {source} | {data['files']} | {data['pages']} | "
            f"{data['bytes'] / (1024 * 1024):.2f} | {data['tokens']} | "
            f"{'; '.join(licences)} |"
        )

    dataset += [
        "",
        (
            f"**Total:** {sum(x['files'] for x in totals.values())} files, "
            f"{total_pages} pages, {text_mb:.2f} MB, {total_tokens:,} tokens."
        ),
        "",
        "<!-- generated:end -->",
        "",
        "## Known gaps",
        "",
        "- Pro Git chapters 1-3 and 7 are not yet collected; the current corpus contains Git reference documentation only.",
        "- The 40-command start target is not yet fully verified.",
    ]

    capacity = [
        "# Capacity plan: GitGuru",
        "",
        "Full corpus target: All reference pages, the full Pro Git book and release notes from 2.30 onwards (2,000+ pages)",
        "",
        "<!-- generated:start -->",
        "",
        "| Measure | Current corpus | Full corpus estimate |",
        "|---|---:|---:|",
        f"| Pages | {total_pages:,} | {target_pages:,} |",
        f"| Tokens | {total_tokens:,} | {full_tokens:,.0f} |",
        f"| Tokens per page | {tokens_per_page:,.0f} | {tokens_per_page:,.0f} |",
        f"| Chunks ({args.chunk_tokens} tokens) | {int((total_tokens + args.chunk_tokens - 1) // args.chunk_tokens):,} | {chunks:,} |",
        f"| Embedding cost | — | Rs {embed_cost:,.2f} |",
        f"| Vector storage | — | {vector_mb:,.2f} MB |",
        f"| Text storage | {text_mb:,.2f} MB | {projected_text_mb:,.2f} MB |",
        "",
        "<!-- generated:end -->",
        "",
        "## What I conclude",
        "",
        f"1. Embedding cost is estimated at Rs {embed_cost:,.2f} for {full_tokens:,.0f} tokens; this is a one-time estimate.",
        "2. Compare the estimated text and vector storage above with the storage limit shown on your database dashboard.",
        "3. The least certain number is tokens per page; measure it again after collecting a larger and more varied sample.",
        (
            "4. At 10 times the corpus size, tokens, chunks, embedding cost and storage will be approximately 10 times larger. "
            "Recheck database capacity and embedding budget before expanding."
        ),
    ]

    (ROOT / "DATASET.md").write_text("\n".join(dataset) + "\n", encoding="utf-8")
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "CAPACITY.md").write_text("\n".join(capacity) + "\n", encoding="utf-8")

    print(
        f"files={sum(x['files'] for x in totals.values())} "
        f"pages={total_pages} -> wrote DATASET.md and docs/CAPACITY.md"
    )


if __name__ == "__main__":
    main()
