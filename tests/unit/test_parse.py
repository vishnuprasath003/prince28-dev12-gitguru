from pathlib import Path

import pymupdf
import pytest

from gitguru.ingest.parse import (
    ParseError,
    clean_text,
    drop_repeated_lines,
    finish,
    heading_title,
    headings_in,
    markup_to_markdown,
    parse_file,
    parse_html,
    parse_pdf_pymupdf,
    parse_text,
    split_pages,
    with_heading_paths,
)


def test_clean_text_normalizes_unicode():
    assert clean_text("ﬁle") == "file"


def test_clean_text_removes_null_characters():
    assert clean_text("hello\x00world") == "helloworld"


def test_clean_text_joins_hyphenated_words():
    assert clean_text("treat-\nment") == "treatment"


def test_clean_text_removes_extra_spaces():
    assert clean_text("hello   world") == "hello world"


def test_drop_repeated_lines_removes_headers():
    pages = [
        "Git Documentation\nContent one\nFooter",
        "Git Documentation\nContent two\nFooter",
        "Git Documentation\nContent three\nFooter",
        "Git Documentation\nContent four\nFooter",
    ]
    result = drop_repeated_lines(pages)
    assert all("Git Documentation" not in page for page in result)


def test_heading_title_removes_anchor():
    assert heading_title("First Steps { #first-steps }") == "First Steps"


def test_headings_in_finds_markdown_headings():
    found, _ = headings_in("# Main\n## Child")
    assert found == [(1, "Main"), (2, "Child")]


def test_headings_in_ignores_code_blocks():
    found, _ = headings_in("```python\n# Not a heading\n```\n# Real heading")
    assert found == [(1, "Real heading")]


def test_with_heading_paths_tracks_sections():
    pages = with_heading_paths(["# Main\n\nText", "More text"])
    assert pages[0].headings == []
    assert pages[1].headings == ["Main"]


def test_finish_uses_first_heading_as_title():
    doc = finish("plain", "text", "filename", ["# Actual Title\n\nSome content"])
    assert doc.title == "Actual Title"


def test_split_pages_splits_long_text():
    result = split_pages("A" * 100 + "\n\n" + "B" * 100, size=120)
    assert len(result) == 2


def test_markup_to_markdown_converts_asciidoc():
    result = markup_to_markdown("= Main\n\n== Child", ".adoc")
    assert "# Main" in result
    assert "## Child" in result


def test_parse_text_reads_markdown(tmp_path: Path):
    path = tmp_path / "guide.md"
    path.write_text("# Git Guide\n\nGit tracks changes.", encoding="utf-8")
    doc = parse_text(path)
    assert doc.kind == "text"
    assert doc.title == "Git Guide"
    assert doc.pages[0].page_no == 1


def test_parse_html_extracts_main_content(tmp_path: Path):
    path = tmp_path / "guide.html"
    path.write_text(
        "<html><head><title>Git Guide</title></head>"
        "<body><main><h1>Git Guide</h1>"
        "<p>This is useful documentation about Git commands.</p>"
        "<p>It contains enough information for extraction.</p>"
        "</main></body></html>",
        encoding="utf-8",
    )
    doc = parse_html(path)
    assert doc.kind == "html"
    assert "Git Guide" in doc.title


def test_pdf_parsers_extract_text(tmp_path: Path):
    path = tmp_path / "guide.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Git Documentation\nThis document explains version control and Git commands.",
        fontsize=12,
    )
    doc.save(path)
    doc.close()

    result = parse_pdf_pymupdf(path)
    assert result.kind == "pdf"
    assert "Git Documentation" in result.pages[0].text


def test_parse_file_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "archive.zip"
    path.write_text("not a supported document", encoding="utf-8")

    with pytest.raises(ParseError) as exc:
        parse_file(path)

    assert exc.value.reason == "unsupported_type"
