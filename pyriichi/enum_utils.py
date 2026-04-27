from __future__ import annotations

from enum import Enum
from typing import Optional


class TranslatableEnum(Enum):
    """Enum base class with multilingual display names."""

    def __new__(cls, code: str, zh: str, ja: str, en: Optional[str] = None):
        obj = object.__new__(cls)
        obj._value_ = code
        obj._zh = zh  # pyright: ignore[reportAttributeAccessIssue]
        obj._ja = ja  # pyright: ignore[reportAttributeAccessIssue]
        obj._en = en  # pyright: ignore[reportAttributeAccessIssue]
        return obj

    @property
    def code(self) -> str:
        """Enum code value."""
        return str(self.value)

    @property
    def zh(self) -> str:
        """Traditional Chinese display name."""
        return self._zh  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def ja(self) -> str:
        """Japanese display name."""
        return self._ja  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def en(self) -> str:
        """English display name, falling back to the code if unset."""
        return (
            self._en if self._en is not None else str(self.value)
        )  # pyright: ignore[reportAttributeAccessIssue]
