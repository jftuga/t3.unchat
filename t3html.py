# Converts exported t3.chat markdown files to styled HTML.
# Walks a directory tree of .md files produced by t3export.py and generates
# a companion .html file for each one with embedded CSS for readability.

import argparse
import calendar
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter


PYGMENTS_CSS = HtmlFormatter(style="default").get_style_defs(".codehilite")

CSS = f"""\
body {{
    max-width: 48em;
    margin: 2em auto;
    padding: 0 1em;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 1rem;
    line-height: 1.6;
    color: #1a1a1a;
    background: #fdfdfd;
}}
h1 {{ font-size: 1.6em; border-bottom: 1px solid #ddd; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.3em; margin-top: 1.5em; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 1.5em 0; }}
.codehilite {{
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.8em 1em;
    overflow-x: auto;
    font-size: 0.9em;
}}
pre {{
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.8em 1em;
    overflow-x: auto;
    font-size: 0.9em;
}}
code {{
    background: #f5f5f5;
    padding: 0.15em 0.3em;
    border-radius: 3px;
    font-size: 0.9em;
}}
pre code {{ background: none; padding: 0; border-radius: 0; }}
blockquote {{
    border-left: 3px solid #ccc;
    margin: 1em 0;
    padding: 0.5em 1em;
    color: #555;
}}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.5em 0.8em; text-align: left; }}
th {{ background: #f5f5f5; }}
a {{ color: #0366d6; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
{PYGMENTS_CSS}
"""

MD_EXTENSIONS = [
    "fenced_code",
    "codehilite",
    "tables",
    "nl2br",
]
MD_EXTENSION_CONFIGS = {
    "codehilite": {
        "guess_lang": True,
        "noclasses": False,
    },
}


def render_html(md_text: str, title: str) -> str:
    """Convert markdown text to a complete styled HTML document.

    Args:
        md_text: Raw markdown content.
        title: Title for the HTML <title> tag.

    Returns:
        A complete HTML document string.
    """
    body = markdown.markdown(
        md_text,
        extensions=MD_EXTENSIONS,
        extension_configs=MD_EXTENSION_CONFIGS,
    )
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<title>{title}</title>\n"
        f"<style>\n{CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def is_pinned(md_text: str) -> bool:
    """Check if the thread metadata in the markdown indicates it was pinned.

    Args:
        md_text: Raw markdown content.

    Returns:
        True if the thread was pinned, False otherwise.
    """
    match = re.search(r"```json\s*\n({.*?})\s*\n```", md_text, re.DOTALL)
    if not match:
        return False
    try:
        metadata = json.loads(match.group(1))
        return metadata.get("pinned", False) is True
    except json.JSONDecodeError:
        return False


def add_pin_icon(html: str) -> str:
    """Insert a pin icon after the first h1 tag's content.

    Args:
        html: The complete HTML document string.

    Returns:
        The HTML with a pin icon appended to the first h1 element.
    """
    return html.replace("</h1>", ' &#x1F4CC;</h1>', 1)


def convert_file(md_path: Path) -> None:
    """Convert a single markdown file to a companion HTML file.

    Args:
        md_path: Path to the .md file.
    """
    md_text = md_path.read_text(encoding="utf-8")
    title = md_path.stem.split("--", 1)[-1].replace("_", " ")
    html = render_html(md_text, title)
    if is_pinned(md_text):
        html = add_pin_icon(html)
    html_path = md_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")


def convert_tree(root: Path) -> int:
    """Walk a directory tree and convert all .md files to HTML.

    Args:
        root: Root directory to walk.

    Returns:
        The number of HTML files written.
    """
    count = 0
    for md_path in sorted(root.rglob("*.md")):
        convert_file(md_path)
        count += 1
    return count


INDEX_CSS = """\
body {
    max-width: 60em;
    margin: 2em auto;
    padding: 0 1em;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 1rem;
    line-height: 1.6;
    color: #1a1a1a;
    background: #fdfdfd;
}
h1 { font-size: 1.6em; border-bottom: 1px solid #ddd; padding-bottom: 0.3em; position: sticky; top: 0; background: #fdfdfd; z-index: 1; }
h2 { font-size: 1.3em; margin-top: 1.8em; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 0.5em 0 1.5em 0; }
th, td { border: 1px solid #ddd; padding: 0.4em 0.8em; text-align: left; }
th { background: #f5f5f5; }
td:first-child { white-space: nowrap; width: 7em; }
a { color: #0366d6; text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def extract_metadata(md_path: Path) -> dict | None:
    """Extract the thread metadata JSON from a markdown file.

    Args:
        md_path: Path to the .md file.

    Returns:
        The parsed metadata dict, or None if not found.
    """
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8")
    match = re.search(
        r"(?:^|\n)#+\s*Metadata\s*\n+```json\s*\n({.*?})\s*\n```",
        text,
        re.DOTALL,
    )
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def parse_html_entry(html_path: Path, root: Path) -> tuple[str, str, str, float] | None:
    """Extract the date, title, relative path, and sort timestamp from an HTML file.

    Expects filenames like '20250307--Some_Title.html'. Returns None if
    the filename does not match the expected pattern.

    Args:
        html_path: Absolute path to the HTML file.
        root: Root output directory for computing relative paths.

    Returns:
        A tuple of (YYYY-mm-dd date string, display title, relative path,
        createdAt timestamp for sorting) or None if the filename cannot be parsed.
    """
    stem = html_path.stem
    if "--" not in stem:
        return None
    date_part, title_part = stem.split("--", 1)
    if len(date_part) != 8 or not date_part.isdigit():
        return None
    date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    title = title_part.replace("_", " ")
    # Strip numeric duplicate suffix like "_2", "_3"
    title = re.sub(r" (\d+)$", r" (\1)", title)
    rel_path = html_path.relative_to(root).as_posix()
    md_path = html_path.with_suffix(".md")
    metadata = extract_metadata(md_path)
    created_at = 0.0
    if metadata:
        if metadata.get("pinned", False) is True:
            title = "\U0001f4cc " + title
        created_at = metadata.get("createdAt", 0.0)
    return date_str, title, rel_path, created_at


def month_label(year_month: str) -> str:
    """Convert a 'YYYY/mm' string to a readable 'Month YYYY' label.

    Args:
        year_month: String like '2025/03'.

    Returns:
        A string like 'March 2025'.
    """
    year, month = year_month.split("/")
    return f"{calendar.month_name[int(month)]} {year}"


def build_index(root: Path, source: str = "") -> None:
    """Build a top-level index.html linking to all thread HTML files.

    Groups threads by YYYY/mm directory in reverse chronological order,
    with each group rendered as a table of date + hyperlinked title.

    Args:
        root: Root output directory containing the YYYY/mm/ structure.
        source: Optional source filename to display below the title.
    """
    entries_by_month: dict[str, list[tuple[str, str, str, float]]] = defaultdict(list)

    for html_path in sorted(root.rglob("*.html")):
        if html_path.name == "index.html":
            continue
        entry = parse_html_entry(html_path, root)
        if entry is None:
            continue
        date_str, title, rel_path, created_at = entry
        year_month = f"{date_str[:4]}/{date_str[5:7]}"
        entries_by_month[year_month].append((date_str, title, rel_path, created_at))

    # Build HTML
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>t3.unchat Export Index</title>",
        f"<style>\n{INDEX_CSS}</style>",
        "</head>",
        "<body>",
        "<h1>t3.unchat Export Index"
        + (f'<br><small style="font-size: 0.5em; color: #666; font-weight: normal;">'
           f"source: {Path(source).name}</small>" if source else "")
        + "</h1>",
    ]

    for year_month in sorted(entries_by_month.keys(), reverse=True):
        # Sort by createdAt timestamp (index 3) descending for full precision
        entries = sorted(entries_by_month[year_month], key=lambda e: e[3], reverse=True)
        parts.append(f"<h2>{month_label(year_month)} ({len(entries)})</h2>")
        parts.append("<table>")
        parts.append("<tr><th>Date</th><th>Title</th></tr>")
        for date_str, title, rel_path, _ in entries:
            parts.append(
                f'<tr><td>{date_str}</td>'
                f'<td><a href="{rel_path}">{title}</a></td></tr>'
            )
        parts.append("</table>")

    parts.append("</body>")
    parts.append("</html>")
    parts.append("")

    index_path = root / "index.html"
    index_path.write_text("\n".join(parts), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional list of arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace with directory path.
    """
    parser = argparse.ArgumentParser(
        description="Convert t3export markdown files to styled HTML."
    )
    parser.add_argument(
        "directory",
        help="Root directory containing .md files to convert.",
    )
    parser.add_argument(
        "-s",
        "--source",
        default="",
        help="Source export filename to display in the index header.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the t3html CLI.

    Args:
        argv: Optional list of arguments for testing.
    """
    args = parse_args(argv)
    root = Path(args.directory)
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)
    count = convert_tree(root)
    build_index(root, source=args.source)
    print(f"Converted {count} markdown files to HTML in {root}/")
    print(f"Created {root}/index.html")


if __name__ == "__main__":
    main()
