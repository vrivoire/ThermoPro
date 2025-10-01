"""Base Peak module."""

import datetime

from hydroqc.error import HydroQcCPCPeakError
from hydroqc.timerange import TimeRange
from hydroqc.utils import EST_TIMEZONE


class BasePeak(TimeRange):
    """Base peak class."""

    _start_date: datetime.datetime
    _end_date: datetime.datetime

    def __init__(self, start_date: datetime.datetime, end_date: datetime.datetime):
        """Build base peak."""
        if not start_date.tzinfo:
            self._start_date = start_date.astimezone(EST_TIMEZONE)
        else:
            self._start_date = start_date
        if not end_date.tzinfo:
            self._end_date = end_date.astimezone(EST_TIMEZONE)
        else:
            self._end_date = end_date

        super().__init__(self.start_date, self.end_date, is_critical=False)

    @property
    def is_morning(self) -> bool:
        """Return True if it's a morning peak."""
        return self._start_date.hour < 12

    @property
    def is_evening(self) -> bool:
        """Return True if it's a evening peak."""
        return self._start_date.hour > 12

    @property
    def day(self) -> datetime.date:
        """Get the day, without time, of the peak."""
        return self._start_date.date()

    @property
    def date(self) -> datetime.date:
        """DEPRECATED - Get the day, without time, of the peak."""
        return self.day

    @property
    def start_date(self) -> datetime.datetime:
        """Get the start date of the peak."""
        return self._start_date

    @property
    def end_date(self) -> datetime.datetime:
        """Get the end date of the peak."""
        return self._end_date

    @property
    def morning_evening(self) -> str:
        """Return evening or morning peak value."""
        if self.is_morning:
            return "morning"
        if self.is_evening:
            return "evening"
        msg = "Can not determine if is morning or evening peak"
        raise HydroQcCPCPeakError(msg)
