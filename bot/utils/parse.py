from __future__ import annotations

import re
import typing as t

from hikari import Attachment, Message

from bot import models

CODE_BLOCK_REGEX = re.compile(r"```(?P<lang>\w*)[\n\s]*(?P<code>(.|\n)*?)```")
CODE_LINE_REGEX = re.compile(r"`(?P<code>[^`\n]+)`")


async def get_codes(message: Message) -> list[models.Code]:
    return [
        *_get_code_blocks(message.content),
        *await _get_code_attachments(message.attachments),
    ]


def _get_code_blocks(content: str | None) -> list[models.Code]:
    if not content:
        return []

    blocks: list[models.Code] = []

    for block in CODE_BLOCK_REGEX.finditer(content):
        dct = block.groupdict()
        code = models.Code(code=dct["code"])
        if language := dct.get("lang"):
            code.language = language
        blocks.append(code)

    content = CODE_BLOCK_REGEX.sub("", content)
    for line in CODE_LINE_REGEX.finditer(content):
        blocks.append(models.Code(code=line.groupdict()["code"]))

    return blocks


async def _get_code_attachments(files: t.Sequence[Attachment]) -> list[models.Code]:
    codes: list[models.Code] = []

    for file in files:
        content = await file.read()
        code = models.Code(code=content.decode(), filename=file.filename)
        if extension := file.extension:
            code.language = extension
        codes.append(code)

    return codes
