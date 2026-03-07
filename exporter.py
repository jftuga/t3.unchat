# Orchestrates the export of t3.chat threads and messages to markdown files.
# Loads the JSON export, groups messages by thread, handles duplicate filenames,
# and writes the YYYY/mm/TITLE.md folder structure.

import json
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

from message import Message
from t3_thread import T3Thread


class Exporter:
    """Exports t3.chat JSON data into a structured markdown folder hierarchy.

    Reads the t3.json export file, groups messages by their thread, sorts
    them chronologically, and writes one markdown file per thread into a
    YYYY/mm/ directory structure under the specified output path.
    """

    def __init__(self, json_path: str, output_dir: str, tz: ZoneInfo) -> None:
        """Initialize the exporter with input and output paths.

        Args:
            json_path: Path to the t3.json export file.
            output_dir: Root directory for the markdown output.
            tz: Timezone for displaying computed datetimes.
        """
        self.json_path = Path(json_path)
        self.output_dir = Path(output_dir)
        self.tz = tz

    def load(self) -> tuple[list[T3Thread], dict[str, list[Message]]]:
        """Load and parse the JSON export into threads and grouped messages.

        Returns:
            A tuple of (list of T3Thread objects, dict mapping threadId to
            sorted list of Message objects).

        Raises:
            FileNotFoundError: If the JSON file does not exist.
            json.JSONDecodeError: If the JSON file is malformed.
        """
        with open(self.json_path, encoding="utf-8") as f:
            data = json.load(f)

        threads = [T3Thread.from_dict(t) for t in data["threads"]]
        threads.sort(key=lambda t: t.created_at)

        messages_by_thread: dict[str, list[Message]] = defaultdict(list)
        for m in data["messages"]:
            msg = Message.from_dict(m)
            messages_by_thread[msg.thread_id].append(msg)

        for msg_list in messages_by_thread.values():
            msg_list.sort(key=lambda m: m.created_at)

        return threads, messages_by_thread

    def render_thread(self, thread: T3Thread, messages: list[Message]) -> str:
        """Render a single thread and its messages as a complete markdown document.

        Args:
            thread: The thread to render.
            messages: Sorted list of messages belonging to this thread.

        Returns:
            A complete markdown string for the thread file.
        """
        parts: list[str] = [f"# {thread.title}", ""]

        for i, msg in enumerate(messages):
            parts.append(msg.to_markdown())
            if i < len(messages) - 1:
                parts.append("")
                parts.append("---")
                parts.append("")

        parts.append("")
        parts.append("---")
        parts.append("")
        parts.append("# Metadata")
        parts.append("```json")
        parts.append(thread.metadata_json())
        parts.append("```")
        parts.append("")
        parts.append("# Computed Date Times")
        parts.append(thread.computed_datetimes(self.tz))
        parts.append("")

        return "\n".join(parts)

    def resolve_filename(self, folder: Path, base_name: str, seen: dict[str, int]) -> str:
        """Resolve a unique filename within a folder, adding numeric suffixes for duplicates.

        Args:
            folder: The target directory path.
            base_name: The sanitized filename stem (without extension).
            seen: A dict tracking how many times each folder/name combo has been used.

        Returns:
            A unique filename string (with .md extension).
        """
        key = f"{folder}/{base_name}".lower()
        count = seen.get(key, 0)
        seen[key] = count + 1
        if count == 0:
            return f"{base_name}.md"
        return f"{base_name}_{count + 1}.md"

    def export(self) -> int:
        """Run the full export, writing markdown files to the output directory.

        Returns:
            The number of thread files written.
        """
        threads, messages_by_thread = self.load()
        seen: dict[str, int] = {}
        count = 0

        for thread in threads:
            messages = messages_by_thread.get(thread.thread_id, [])
            if not messages:
                continue

            folder = self.output_dir / thread.folder_path()
            folder.mkdir(parents=True, exist_ok=True)

            base_name = thread.filename_stem()
            filename = self.resolve_filename(folder, base_name, seen)
            filepath = folder / filename

            content = self.render_thread(thread, messages)
            filepath.write_text(content, encoding="utf-8")
            count += 1

        return count
