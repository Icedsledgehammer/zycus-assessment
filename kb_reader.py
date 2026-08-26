from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class KBChunk:
    """A single retrievable piece of knowledge-base content."""

    text: str
    source: str
    headings: dict[str, str] = field(default_factory=dict)
    chunk_type: str = "text"


def read_markdown_files(file_path: Path) -> str:
    """Read a markdown file and return its contents"""

    return file_path.read_text(encoding="utf-8")


def split_sections(content: str) -> list[str]:
    """Split a markdown file using horizontal rules (---)
    The Zycus data schema says so in the document provided"""

    sections = re.split(r"(?m)^\s*---\s*$", content)

    return [section.strip() for section in sections if section.strip()]


def extract_heading(line: str) -> tuple[int, str] | None:
    """
    Extract the heading level and title from a markdown heading.

    Example:
        '# AnalyticsHub' -> (1, 'AnalyticsHub')
        '## Overview'   -> (2, 'Overview')
    """

    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)

    if not match:
        return None

    level = len(match.group(1))
    title = match.group(2).strip()

    return level, title


def is_table_row(line: str) -> bool:
    """Return true if the line looks like a markdown table row, otherwise false."""

    stripped = line.strip()

    return stripped.startswith("|") and stripped.endswith("|")


def is_table_separator(line: str) -> bool:
    """
    Return True if the line is a Markdown table separator.

    Example:
        |------|---------|
    """

    cells = line.strip().strip("|").split("|")

    if not cells:
        return False

    return all(re.fullmatch(r"\s*:?-+:?\s*", cell) is not None for cell in cells)


def create_chunk(
    text: str,
    source: str,
    headings: dict[int, str],
    chunk_type: str = "text",
) -> KBChunk | None:
    """Create a KBChunk if the supplied text is non-empty."""

    cleaned_text = text.strip()

    if not cleaned_text:
        return None

    metadata = {f"h{level}": title for level, title in sorted(headings.items())}

    return KBChunk(
        text=cleaned_text,
        source=source,
        headings=metadata,
        chunk_type=chunk_type,
    )


def parse_section(
    section: str,
    source: str,
    heading_state: dict[int, str],
) -> list[KBChunk]:
    """
    Convert one major Markdown section into KB chunks.

    Normal text remains together within the section.
    Markdown table rows become individual chunks.
    """

    lines = section.splitlines()

    chunks: list[KBChunk] = []
    current_text: list[str] = []

    current_headings = heading_state.copy()
    table_started = False

    def flush_text() -> None:
        """Turn accumulated normal text into a chunk."""

        if not current_text:
            return

        chunk = create_chunk(
            text="\n".join(current_text),
            source=source,
            headings=current_headings,
            chunk_type="text",
        )

        if chunk:
            chunks.append(chunk)

        current_text.clear()

    for line in lines:
        heading = extract_heading(line)

        if heading:
            flush_text()

            level, title = heading

            current_headings[level] = title

            # Remove headings below the current level.
            for deeper_level in range(level + 1, 7):
                current_headings.pop(deeper_level, None)

            continue

        if is_table_row(line):
            flush_text()

            # Ignore Markdown table separator rows.
            if is_table_separator(line):
                continue

            if not table_started:
                table_started = True
                continue

            chunk = create_chunk(
                text=line.strip(),
                source=source,
                headings=current_headings,
                chunk_type="table_row",
            )

            if chunk:
                chunks.append(chunk)

            continue

        current_text.append(line)

    flush_text()

    # Update the caller's heading state so that it survives
    # across multiple '---' sections.
    heading_state.clear()
    heading_state.update(current_headings)

    return chunks


def load_knowledge_base(kb_root: Path) -> list[KBChunk]:
    """
    Read all Markdown documents in the knowledge base
    and convert them into structured chunks.
    """

    chunks: list[KBChunk] = []

    markdown_files = sorted(kb_root.rglob("*.md"))

    for file_path in markdown_files:
        content = read_markdown_files(file_path)

        sections = split_sections(content)

        heading_state: dict[int, str] = {}

        relative_source = str(file_path.relative_to(kb_root))

        for section in sections:
            chunks.extend(
                parse_section(
                    section=section,
                    source=relative_source,
                    heading_state=heading_state,
                )
            )

    return chunks


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]

    kb_root = project_root / "knowledge-base"

    chunks = load_knowledge_base(kb_root)

    print(f"Loaded {len(chunks)} chunks.")

    for index, chunk in enumerate(chunks[:10], start=1):
        print(f"\n--- Chunk {index} ---")
        print(f"Source: {chunk.source}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Headings: {chunk.headings}")
        print(f"Text:\n{chunk.text[:500]}")
