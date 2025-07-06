"""Data models for VoxVibe."""

from typing import TypedDict


class WindowInfo(TypedDict):
    """Type definition for window information."""
    title: str
    wm_class: str
    id: int