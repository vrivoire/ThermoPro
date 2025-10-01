"""CPC processing."""

import datetime
import logging
from typing import Any, Generic, TypeVar

from hydroqc import utils
from hydroqc.error import HydroQcCPCPeakError
from hydroqc.hydro_api.client import HydroClient
from hydroqc.peak.consts import DEFAULT_PRE_HEAT_DURATION
from hydroqc.peak.cpc.peak import Peak as CPCPeak
from hydroqc.peak.dpc.peak import Peak as DPCPeak
from hydroqc.types import OpenDataPeakEvent, OpenDataPeakEventOffer

T = TypeVar("T", DPCPeak, CPCPeak)


class BasePeakHandler(Generic[T]):
    """Common peak handler module."""

    _offer_code: OpenDataPeakEventOffer

    def __init__(
        self,
        applicant_id: str,
        customer_id: str,
        contract_id: str,
        hydro_client: HydroClient,
        logger: logging.Logger,
    ):
        """CPC constructor."""
        self._no_partenaire_demandeur: str = applicant_id
        self._no_partenaire_titulaire: str = customer_id
        self._no_contrat: str = contract_id
        self._hydro_client: HydroClient = hydro_client
        self._logger: logging.Logger = logger

        self._raw_open_data: list[OpenDataPeakEvent] = []
        self._preheat_duration = DEFAULT_PRE_HEAT_DURATION

    # Basics
    @property
    def applicant_id(self) -> str:
        """Get applicant id."""
        return self._no_partenaire_demandeur

    @property
    def customer_id(self) -> str:
        """Get customer id."""
        return self._no_partenaire_titulaire

    @property
    def contract_id(self) -> str:
        """Get contract id."""
        return self._no_contrat

    @property
    def offer_code(self) -> str:
        """Get offer code of the open data page."""
        return self._offer_code

    def set_preheat_duration(self, duration: int) -> None:
        """Set preheat duration in minutes."""
        self._preheat_duration = duration

    # Fetch raw data
    async def refresh_data(self) -> None:
        """Get data from HydroQuebec web site."""
        raise NotImplementedError

    # Fetch raw data using open data url
    async def refresh_open_data(self) -> None:
        """Get data from HydroQuebec peak open data url."""
        self._logger.debug("Fetching peak open data from HydroQuebec...")
        self._raw_open_data = await self._hydro_client.get_open_data_peaks(
            self._offer_code
        )
        self._logger.debug("Data fetched from peak open data HydroQuebec...")
        # Ensure that peaks are sorted by date
        self._raw_open_data.sort(key=lambda x: (x["dateDebut"]))

    @property
    def raw_data(self) -> Any:
        """Return raw collected data."""
        raise NotImplementedError

    @property
    def raw_open_data(self) -> list[OpenDataPeakEvent]:
        """Return raw collected open data."""
        return self._raw_open_data

    # general data
    @property
    def winter_start_date(self) -> datetime.datetime:
        """Get start date of the peaks period."""
        today = datetime.date.today()
        if today.month >= 12:
            return datetime.datetime.strptime(
                f"{today.year}-12-01T05:00:00.000+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
            ).astimezone(utils.EST_TIMEZONE)
        if today.month <= 3:
            return datetime.datetime.strptime(
                f"{today.year-1}-12-01T05:00:00.000+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
            ).astimezone(utils.EST_TIMEZONE)
        # TODO ensure the value
        # today.month > 4
        return datetime.datetime.strptime(
            f"{today.year}-12-01T05:00:00.000+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
        ).astimezone(utils.EST_TIMEZONE)

    @property
    def winter_end_date(self) -> datetime.datetime:
        """Get end date of the peaks period."""
        today = datetime.date.today()
        if today.month >= 12:
            return datetime.datetime.strptime(
                f"{today.year+1}-03-31T04:00:00.000+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
            ).astimezone(utils.EST_TIMEZONE)
        if today.month <= 3:
            return datetime.datetime.strptime(
                f"{today.year}-03-31T04:00:00.000+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
            ).astimezone(utils.EST_TIMEZONE)
        # TODO ensure the value
        # today.month > 4
        return datetime.datetime.strptime(
            f"{today.year+1}-03-31T04:00:00.000+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
        ).astimezone(utils.EST_TIMEZONE)

    @property
    def is_winter(self) -> bool:
        """Return true if we are in winter period."""
        return self.winter_start_date <= utils.now() <= self.winter_end_date

    # Peaks data
    @property
    def peaks(self) -> list[T]:
        """List all peaks of the current winter."""
        return self._get_peaks()

    def _get_peaks(self) -> list[T]:
        """Get all peaks of the current winter."""
        raise NotImplementedError

    @property
    def sonic(self) -> list[T]:
        """Piaf's joke."""
        return self._get_peaks()

    # Current peak
    @property
    def current_peak(self) -> T | None:
        """Get current peak.

        Return None if no peak is currently running
        FIXME This could be USELESS
        """
        now = utils.now()
        peaks: list[T] = [p for p in self.peaks if p.start_date < now < p.end_date]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one current peak !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    # In progress
    # Next peak
    @property
    def next_peak(self) -> T | None:
        """Get next peak or current peak."""
        return self._get_next_peak()

    def _get_next_peak(self) -> T | None:
        """Get next peak or current peak."""
        now = utils.now()
        peaks: list[T] = [p for p in self.peaks if now < p.end_date]
        if not peaks:  # pylint: disable=consider-using-assignment-expr
            return None
        next_peak = min(peaks, key=lambda x: x.start_date)
        return next_peak

    # Today peaks
    @property
    def today_morning_peak(self) -> T | None:
        """Get the peak of today morning."""
        now = utils.now()
        peaks: list[T] = [p for p in self.peaks if p.day == now.date() and p.is_morning]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one morning peak today !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    @property
    def today_evening_peak(self) -> T | None:
        """Get the peak of today evening."""
        now = utils.now()
        peaks: list[T] = [p for p in self.peaks if p.day == now.date() and p.is_evening]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one evening peak today !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    # Tomorrow Peaks
    @property
    def tomorrow_morning_peak(self) -> T | None:
        """Get the peak of tomorrow morning."""
        now = utils.now()
        peaks: list[T] = [
            p
            for p in self.peaks
            if p.day == now.date() + datetime.timedelta(days=1) and p.is_morning
        ]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one morning peak tomorrow !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    @property
    def tomorrow_evening_peak(self) -> T | None:
        """Get the peak of tomorrow evening."""
        now = utils.now()
        peaks: list[T] = [
            p
            for p in self.peaks
            if p.day == now.date() + datetime.timedelta(days=1) and p.is_evening
        ]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one evening peak tomorrow !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    # Yesterday peaks
    @property
    def yesterday_morning_peak(self) -> T | None:
        """Get the peak of yesterday morning."""
        now = utils.now()
        peaks: list[T] = [
            p
            for p in self.peaks
            if p.day == now.date() - datetime.timedelta(days=1) and p.is_morning
        ]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one morning peak yesterday !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    @property
    def yesterday_evening_peak(self) -> T | None:
        """Get the peak of yesterday evening."""
        now = utils.now()
        peaks: list[T] = [
            p
            for p in self.peaks
            if p.day == now.date() - datetime.timedelta(days=1) and p.is_evening
        ]
        if len(peaks) > 1:
            raise HydroQcCPCPeakError("There is more than one evening peak yesterday !")
        if len(peaks) == 1:
            return peaks[0]
        return None

    @property
    def preheat_in_progress(self) -> bool:
        """Get the preheat state.

        Returns True if we have a preheat period is in progress.
        """
        now = utils.now()
        if self.next_peak is None:
            return False
        return self.next_peak.preheat.start_date < now < self.next_peak.preheat.end_date
