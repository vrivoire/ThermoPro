"""Hydroqc custom types."""

# pylint: disable=invalid-name
from typing import TypedDict

from hydroqc.types.dpc import DPCDataResultsTyping

DTDataResultsTyping = DPCDataResultsTyping


class DTDataTyping(TypedDict, total=True):
    """FlexD data json output format."""

    success: bool
    results: list[DTDataResultsTyping]
