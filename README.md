# t3.unchat

![Code Base: AI Vibes](https://img.shields.io/badge/Code%20Base-AI%20Vibes%20%F0%9F%A4%A0-blue)

Convert [t3.chat](https://t3.chat) JSON data exports into structured markdown and
styled HTML files for offline browsing and archival.

## Overview

t3.chat provides a JSON export of all your conversations. This tool converts that
export into a browsable collection of markdown and HTML files organized by date. Each
conversation thread becomes a pair of files (`.md` and `.html`) in a `YYYY/mm/`
directory structure, with a top-level `index.html` for navigation.

## Disclaimer

This program was vibe-coded by `Claude Opus 4.6`. As such, the author can't be held responsible for incorrect results. Please verify any and all output.

## Features

- Parses the `threads-export-YYYY-mm-ddT1HH_MM_SS.sssZ.json` export and maps messages to their corresponding threads
- Generates one markdown file per thread with user/assistant message pairs
- Produces styled HTML with syntax-highlighted code blocks (via Pygments)
- Creates a top-level `index.html` with all threads grouped by month in reverse
  chronological order, including within the same day
- Pinned threads are marked with a pin icon in both the HTML page title and the index
- Each markdown file includes a **Metadata** section with the full original thread JSON
  and a **Computed Date Times** section with human-readable timestamps
- Handles duplicate thread titles with numeric suffixes (e.g., `Title_2.md`)
- Case-insensitive duplicate detection for macOS/Windows filesystem compatibility
- Filenames are sanitized to remove problematic characters, with spaces converted to
  underscores and a maximum length of 80 characters
- Configurable timezone for computed datetimes (defaults to US/Eastern)

## Attachment Limitations

The t3.chat JSON export includes attachment IDs referenced by messages, but there is
no way to map these attachment IDs to actual files. The export does not contain
attachment content, filenames, URLs, or any other recoverable data about the
attachments. Messages that referenced attachments will display placeholder text like
`[Attachment: j456jsa24jabccv0thtfzexyz123d27s]` in the output.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Dependencies

- [markdown](https://pypi.org/project/Markdown/) -- markdown to HTML conversion with
  fenced code block, table, and code highlighting extensions
- [Pygments](https://pypi.org/project/Pygments/) -- syntax highlighting for code blocks
  in the HTML output

## Installation

```bash
git clone https://github.com/jftuga/t3.unchat.git
cd t3.unchat
uv sync
```

## Usage

### Step 1: Export markdown files

```bash
uv run python t3export.py threads-export-YYYY-mm-ddT1HH_MM_SS.sssZ.json -o output
```

**Options:**

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Root output directory (default: `output`) |
| `--utc` | Display computed datetimes in UTC instead of US/Eastern |

### Step 2: Generate HTML files and index

```bash
uv run python t3html.py output -s threads-export-YYYY-mm-ddT1HH_MM_SS.sssZ.json
```

**Options:**

| Flag | Description |
|------|-------------|
| `-s`, `--source` | Source export filename to display in the index header |

This converts every `.md` file to a companion `.html` file with embedded CSS and
syntax-highlighted code blocks, then generates a top-level `index.html`.

### Browsing the output

Open `output/index.html` in a web browser. Threads are grouped by month in reverse
chronological order. Each entry links to the styled HTML version of the conversation.

## Output structure

```
output/
  index.html
  2025/
    03/
      20250308--Thread_Title.md
      20250308--Thread_Title.html
      20250309--Another_Thread.md
      20250309--Another_Thread.html
    04/
      ...
  2026/
    ...
```

### Filename format

Each file is named `YYYYmmdd--Sanitized_Title.md` where:

- `YYYYmmdd` is the thread creation date
- `--` is a literal separator
- `Sanitized_Title` has unsafe characters removed, spaces replaced with underscores,
  and is truncated so the full stem stays within 80 characters

### Markdown file structure

Each markdown file contains:

1. **Thread title** as an `h1` heading
2. **Messages** alternating between `## User` and `## Assistant` sections, separated
   by horizontal rules
3. **Metadata** section with the complete original thread JSON
4. **Computed Date Times** section with deduplicated timestamps converted to
   human-readable format in the configured timezone

## Project structure

Files are listed in recommended study order (foundation-first, complexity-last):

1. **`t3_thread.py`** -- `T3Thread` dataclass representing a conversation thread. Handles
   parsing from JSON, filesystem-safe filename generation, metadata serialization, and
   computed datetime conversion.
2. **`message.py`** -- `Message` dataclass representing a single user or assistant
   message. Handles parsing from JSON and rendering to markdown with attachment
   placeholders.
3. **`exporter.py`** -- `Exporter` class that orchestrates the full export. Loads the
   JSON, groups messages by thread, resolves duplicate filenames, and writes the
   markdown files to the date-based directory structure.
4. **`t3export.py`** -- CLI entry point for the markdown export step. Parses arguments
   and delegates to `Exporter`.
5. **`t3html.py`** -- CLI entry point for the HTML conversion step. Converts markdown
   files to styled HTML with syntax highlighting, adds pin icons to pinned threads,
   and builds the `index.html` navigation page.


## Personal Project Disclosure

This program is my own original idea, conceived and developed entirely:

* On my own personal time, outside of work hours
* For my own personal benefit and use
* On my personally owned equipment
* Without using any employer resources, proprietary information, or trade secrets
* Without any connection to my employer's business, products, or services
* Independent of any duties or responsibilities of my employment

This project does not relate to my employer's actual or demonstrably
anticipated research, development, or business activities. No
confidential or proprietary information from any employer was used
in its creation.

