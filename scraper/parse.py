"""Typed helpers that narrow BeautifulSoup lookups to ``Tag``.

``Tag.find`` returns ``Tag | NavigableString | None``; these wrappers narrow to
``Tag`` so call sites stay clean and a missing required element raises a clear
error instead of a cryptic ``AttributeError`` on ``None``.
"""

from typing import Any

from bs4 import Tag


class ElementNotFound(Exception):
    pass


def find_tag(node: Tag, *args: Any, **kwargs: Any) -> Tag:
    found = node.find(*args, **kwargs)
    if not isinstance(found, Tag):
        raise ElementNotFound(f"no Tag matched find({args}, {kwargs})")
    return found


def find_tag_opt(node: Tag, *args: Any, **kwargs: Any) -> Tag | None:
    found = node.find(*args, **kwargs)
    return found if isinstance(found, Tag) else None
