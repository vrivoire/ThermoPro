"""Class describing a period."""

import datetime

from hydroqc.peak.basepeak import BasePeak
from hydroqc.peak.consts import DEFAULT_PRE_HEAT_DURATION
from hydroqc.timerange import TimeRange

__all__ = ["PreHeat", "Peak"]


class PreHeat(TimeRange):
    """This class describe a period object."""

    def __init__(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ):
        """Period constructor."""
        super().__init__(start_date, end_date, True)


class Peak(BasePeak):
    """This class describe a period object."""

    # preheat: PreHeat

    def __init__(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        preheat_duration: int = DEFAULT_PRE_HEAT_DURATION,
    ):
        """Period constructor."""
        self._preheat_duration: int = preheat_duration
        super().__init__(start_date, end_date)
        # For DPC, all peaks are criticals, since peaks
        # exist only when it's needed
        self._is_critical = True

    @property
    def preheat(self) -> PreHeat:
        """Get the preheat period of the peak."""
        preheat_start_date = self.start_date - datetime.timedelta(
            minutes=self._preheat_duration
        )
        return PreHeat(preheat_start_date, self.start_date)
