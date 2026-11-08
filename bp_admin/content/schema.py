import json
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, Self

from flask import render_template

from .sanitize import clean_inline, clean_text

HEADER_LEVELS = (2, 3)
LIST_STYLES = ("ordered", "unordered", "checklist")
EMBED_PREFIXES = {
    "youtube": "https://www.youtube.com/embed/",
    "instagram": "https://www.instagram.com/p/",
}


def _one_of(value: Any, options: Collection[Any]) -> Any:
    if value not in options:
        raise ValueError(f"Unexpected value: {value!r}")
    return value


@dataclass
class FileRef:
    id: int
    url: str | None
    path: str
    name: str | None
    extension: str | None

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            id=int(raw["id"]),
            url=raw["url"],
            path=str(raw["path"]),
            name=raw.get("name"),
            extension=raw.get("extension"),
        )


@dataclass
class ListItem:
    content: str
    items: list["ListItem"]

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            content=clean_inline(raw["content"]),
            items=[cls.parse(item) for item in raw.get("items", [])],
        )


#
# Block data
#


@dataclass
class ParagraphData:
    text: str

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(text=clean_inline(raw["text"]))


@dataclass
class HeaderData:
    text: str
    level: int

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            text=clean_inline(raw["text"]),
            level=_one_of(raw["level"], HEADER_LEVELS),
        )


@dataclass
class ListData:
    style: str
    items: list[ListItem]

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            style=_one_of(raw["style"], LIST_STYLES),
            items=[ListItem.parse(item) for item in raw["items"]],
        )


@dataclass
class ImageData:
    file: FileRef
    caption: str

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            file=FileRef.parse(raw["file"]),
            caption=clean_inline(raw.get("caption", "")),
        )


@dataclass
class EmbedData:
    service: str
    source: str
    embed: str
    width: int
    height: int
    caption: str

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        service = _one_of(raw["service"], EMBED_PREFIXES)
        embed = str(raw["embed"])
        if not embed.startswith(EMBED_PREFIXES[service]):
            raise ValueError(f"Unexpected {service} embed URL: {embed}")
        return cls(
            service=service,
            source=str(raw["source"]),
            embed=embed,
            width=int(raw["width"]),
            height=int(raw["height"]),
            caption=clean_inline(raw.get("caption", "")),
        )


@dataclass
class AttachesData:
    file: FileRef
    title: str

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            file=FileRef.parse(raw["file"]),
            title=clean_text(raw.get("title", "")),
        )


BlockData = ParagraphData | HeaderData | ListData | ImageData | EmbedData | AttachesData

BLOCK_TYPES: dict[str, type[BlockData]] = {
    "paragraph": ParagraphData,
    "header": HeaderData,
    "list": ListData,
    "image": ImageData,
    "embed": EmbedData,
    "attaches": AttachesData,
}


#
# Content
#


@dataclass
class Block:
    id: str
    type: str
    data: BlockData

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        type_ = _one_of(raw["type"], BLOCK_TYPES)
        return cls(
            id=str(raw["id"]),
            type=type_,
            data=BLOCK_TYPES[type_].parse(raw["data"]),
        )


@dataclass
class Content:
    time: int | None
    version: str | None
    blocks: list[Block]

    @property
    def files(self) -> list[FileRef]:
        return [
            block.data.file
            for block in self.blocks
            if isinstance(block.data, ImageData | AttachesData)
        ]

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Self:
        return cls(
            time=raw.get("time"),
            version=raw.get("version"),
            blocks=[Block.parse(block) for block in raw["blocks"]],
        )


def parse_content(text: str, *, block_types: Collection[str] = BLOCK_TYPES) -> Content:
    try:
        raw = json.loads(text)
        if not isinstance(raw["blocks"], list):
            raise ValueError("Content blocks must be a list")
        for block in raw["blocks"]:
            _one_of(block["type"], block_types)
        content = Content.parse(raw)
        if all(
            isinstance(block.data, ParagraphData)
            and not clean_text(block.data.text).strip()
            for block in content.blocks
        ):
            content.blocks = []
        return content
    except (AttributeError, KeyError, TypeError) as error:
        raise ValueError(f"Invalid content: {error!r}") from error


def render_content(content: Content, template_dir: str) -> str:
    return "\n".join(
        render_template(
            f"{template_dir}/{block.type}.html",
            block=block,
            content=content,
        ).strip()
        for block in content.blocks
    )
