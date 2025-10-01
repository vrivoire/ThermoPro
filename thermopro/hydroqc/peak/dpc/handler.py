"""DPC processing."""

import datetime
import logging

from hydroqc import utils
from hydroqc.hydro_api.client import HydroClient
from hydroqc.peak.basepeakhandler import BasePeakHandler
from hydroqc.peak.dpc.peak import Peak
from hydroqc.types import DPCPeakDataTyping, OpenDataPeakEventOffer


class DPCPeakHandler(BasePeakHandler[Peak]):
    """DPC extra logic.

    This class supplements Hydro API data by providing calculated values for pre_heat period,
    anchor period detection as well as next event information.
    """

    _offer_code: OpenDataPeakEventOffer = "TPC-DPC"

    def __init__(
        self,
        applicant_id: str,
        customer_id: str,
        contract_id: str,
        hydro_client: HydroClient,
        logger: logging.Logger,
    ):
        """DPC Peak constructor."""
        super().__init__(
            applicant_id,
            customer_id,
            contract_id,
            hydro_client,
            logger,
        )

        self._raw_data: list[DPCPeakDataTyping] = []

    # Fetch raw data
    async def refresh_data(self) -> None:
        """Get data from HydroQuebec web site."""
        self._logger.debug("Fetching data from HydroQuebec...")
        _raw_data = await self._hydro_client.get_dpc_peak_data(
            self.applicant_id, self.customer_id, self.contract_id
        )

        self._logger.debug("Data fetched from HydroQuebec...")
        # Ensure that peaks are sorted by date
        self._raw_data = []
        if _raw_data["listePeriodePointeCritiqueAujourdhui"]:
            self._raw_data += _raw_data["listePeriodePointeCritiqueAujourdhui"]
        if _raw_data["listePeriodePointeCritiqueDemain"]:
            self._raw_data += _raw_data["listePeriodePointeCritiqueDemain"]

        self._raw_data.sort(key=lambda x: x["dateDebut"])

    @property
    def raw_data(self) -> list[DPCPeakDataTyping]:
        """Return raw collected data."""
        return self._raw_data

    # Internals

    # general data
    @property
    def winter_start_date(self) -> datetime.datetime:
        """Get start date of the dpc peaks period."""
        return super().winter_start_date

    @property
    def winter_end_date(self) -> datetime.datetime:
        """Get end date of the dpc peaks period."""
        return super().winter_end_date

    # Peaks data
    def _get_peaks(self) -> list[Peak]:
        """Get all peaks of the current winter."""
        peak_list: list[Peak] = []
        for raw_peak in self.raw_open_data:
            peak = Peak(
                datetime.datetime.fromisoformat(raw_peak["dateDebut"]),
                datetime.datetime.fromisoformat(raw_peak["dateFin"]),
                preheat_duration=self._preheat_duration,
            )
            peak_list.append(peak)
        peak_list.sort(key=lambda x: x.start_date)
        return peak_list

    # Peak in progress
    @property
    def peak_in_progress(self) -> bool:
        """Is there a peak in progress."""
        return bool(self.current_peak)

    # In progress
    @property
    def current_state(self) -> str:
        """Get the current state of the cpc handler.

        It returns peak or normal
        This value should help for automation.
        """
        now = utils.now()
        if [p for p in self.peaks if p.start_date < now < p.end_date]:
            return "peak"
        return "normal"
