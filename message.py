# Represents a t3.chat message with rendering to markdown format.
# Parses message dicts from the t3.json export and formats them as markdown
# sections with role headers, content, and attachment placeholders.

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Message:
    """Parsed representation of a single t3.chat message.

    Attributes:
        message_id: Unique message identifier.
        thread_id: ID of the thread this message belongs to.
        role: Either 'user' or 'assistant'.
        content: Raw message content (may contain markdown).
        model: LLM model associated with this message.
        created_at: Message creation timestamp.
        attachment_ids: List of attachment IDs referenced by this message.
    """

    message_id: str
    thread_id: str
    role: str
    content: str
    model: str
    created_at: datetime
    attachment_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create a Message from a raw t3.json message dict.

        Args:
            data: Raw message dictionary from the JSON export.

        Returns:
            A Message instance with parsed fields.
        """
        created_ms = data["created_at"]
        created_at = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
        return cls(
            message_id=data["messageId"],
            thread_id=data["threadId"],
            role=data["role"],
            content=data.get("content") or "",
            model=data.get("model") or "unknown",
            created_at=created_at,
            attachment_ids=data.get("attachmentIds") or [],
        )

    def to_markdown(self) -> str:
        """Render this message as a markdown section.

        User messages get a '## User' header, assistant messages get
        '## Assistant'. Attachment IDs are listed as placeholders since
        the export does not include attachment content.

        Returns:
            A markdown-formatted string for this message.
        """
        role_label = "User" if self.role == "user" else "Assistant"
        parts: list[str] = [f"## {role_label}"]

        if self.attachment_ids:
            for aid in self.attachment_ids:
                parts.append(f"[Attachment: {aid}]")
            parts.append("")

        if self.content:
            parts.append(self.content)

        return "\n".join(parts)
