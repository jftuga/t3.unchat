# Represents a t3.chat thread with metadata and filesystem-safe path generation.
# Parses thread dicts from the t3.json export and provides sanitized filenames
# and date-based folder paths for markdown export. Named T3Thread to avoid
# shadowing Python's built-in thread module.

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# Characters to strip from thread titles when generating filenames
_UNSAFE_CHARS = re.compile(r"[#'&?!@$%^*()+=\[\]{}<>|\\/:;\"`,~]")

MAX_FILENAME_LEN = 80

# Canonical timestamp fields to display, mapped from their preferred key.
# Duplicates like created_at/createdAt are collapsed to one entry.
_TIMESTAMP_FIELDS = {
    "createdAt": "Created At",
    "updatedAt": "Updated At",
    "lastMessageAt": "Last Message At",
    "_creationTime": "Creation Time",
}

# Minimum plausible millisecond epoch (2000-01-01)
_MIN_EPOCH_MS = 946_684_800_000


@dataclass
class T3Thread:
    """Parsed representation of a single t3.chat thread.

    Attributes:
        thread_id: Unique identifier linking messages to this thread.
        title: Original thread title.
        model: LLM model used for this thread.
        created_at: Thread creation timestamp.
        pinned: Whether the thread was pinned by the user.
        metadata: Full original thread dict for serialization.
    """

    thread_id: str
    title: str
    model: str
    created_at: datetime
    pinned: bool
    metadata: dict

    @classmethod
    def from_dict(cls, data: dict) -> "T3Thread":
        """Create a T3Thread from a raw t3.json thread dict.

        Args:
            data: Raw thread dictionary from the JSON export.

        Returns:
            A T3Thread instance with parsed fields.
        """
        created_ms = data["createdAt"]
        created_at = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
        return cls(
            thread_id=data["threadId"],
            title=data.get("title", "Untitled"),
            model=data.get("model", "unknown"),
            created_at=created_at,
            pinned=data.get("pinned", False),
            metadata=data,
        )

    def date_prefix(self) -> str:
        """Return the YYYYmmdd date prefix for this thread's filename.

        Returns:
            A string like '20250307'.
        """
        return self.created_at.strftime("%Y%m%d")

    def sanitized_title(self) -> str:
        """Return a filesystem-safe version of the thread title.

        Strips unsafe characters, converts spaces to underscores,
        collapses runs of underscores, and truncates so the full filename
        stem (date_prefix--title) fits within MAX_FILENAME_LEN characters.

        Returns:
            A sanitized string suitable for use as a filename stem.
        """
        name = self.title.replace("\n", " ").replace("\r", " ")
        name = _UNSAFE_CHARS.sub("", name)
        name = name.replace(" ", "_")
        # Collapse multiple underscores/hyphens
        name = re.sub(r"_+", "_", name)
        name = name.strip("_.- ")
        if not name:
            name = "Untitled"
        # Reserve space for "YYYYmmdd--" prefix (10 chars)
        max_title_len = MAX_FILENAME_LEN - 10
        if len(name) > max_title_len:
            name = name[:max_title_len].rstrip("_.- ")
        return name

    def filename_stem(self) -> str:
        """Return the full filename stem: YYYYmmdd--TITLE.

        Returns:
            A string like '20250307--Amazon_CI_Pipelines_Blocking_Gates'.
        """
        return f"{self.date_prefix()}--{self.sanitized_title()}"

    def folder_path(self) -> str:
        """Return the YYYY/mm date-based folder path for this thread.

        Returns:
            A string like '2025/03'.
        """
        return self.created_at.strftime("%Y/%m")

    def metadata_json(self) -> str:
        """Return the full thread metadata as line-delimited JSON.

        Returns:
            A pretty-printed JSON string of the original thread dict.
        """
        return json.dumps(self.metadata, indent=2, default=str)

    def computed_datetimes(self, tz: ZoneInfo) -> str:
        """Return a markdown-formatted table of deduplicated timestamp fields.

        Examines the metadata for known timestamp fields, converts them
        from millisecond epochs to human-readable datetimes in the given
        timezone, and returns a formatted list.

        Args:
            tz: The timezone to convert timestamps into.

        Returns:
            A markdown string with one line per timestamp field.
        """
        lines: list[str] = []
        for key, label in _TIMESTAMP_FIELDS.items():
            value = self.metadata.get(key)
            if not isinstance(value, (int, float)) or value < _MIN_EPOCH_MS:
                continue
            dt = datetime.fromtimestamp(value / 1000, tz=tz)
            lines.append(f"- **{label}**: {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        return "\n".join(lines)
