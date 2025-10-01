"""Utils module."""

import datetime

import pytz

EST_TIMEZONE = pytz.timezone("Canada/Eastern")


def now() -> datetime.datetime:
    """Get EST localized now datetime."""
    return EST_TIMEZONE.localize(datetime.datetime.now())
