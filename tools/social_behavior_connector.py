"""Integration seam for authorized social-platform adapters (no API connection included)."""
from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Mapping


class SocialBehaviorConnector(ABC):
    """Implement a separate adapter per provider after reviewing its API permissions."""

    @abstractmethod
    def fetch(self, start_at: str, end_at: str, account_ids: list[str]) -> Iterable[Mapping[str, object]]:
        """Fetch authorized content-level analytics for a reporting window."""

    @abstractmethod
    def normalize(self, raw_record: Mapping[str, object]) -> dict[str, object]:
        """Map provider-specific metrics into the documented canonical schema."""


class CSVConnector(SocialBehaviorConnector):
    """Local, offline example; does not authenticate or call platform APIs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self, start_at: str = "", end_at: str = "", account_ids: list[str] | None = None):
        with self.path.open(newline="", encoding="utf-8-sig") as handle:
            yield from csv.DictReader(handle)

    def normalize(self, raw_record: Mapping[str, object]) -> dict[str, object]:
        return dict(raw_record)
