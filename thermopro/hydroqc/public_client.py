"""Hydroquebec public data module."""

# from hydroqc.error import HydroQcError
from hydroqc.hydro_api.client import HydroClient
from hydroqc.logger import get_logger
from hydroqc.peak.basepeakhandler import BasePeakHandler
from hydroqc.peak.cpc.handler import CPCPeakHandler
from hydroqc.peak.cpc.peak import Peak as CPCPeak
from hydroqc.peak.dpc.handler import DPCPeakHandler
from hydroqc.peak.dpc.peak import Peak as DPCPeak


class PublicClient:
    """Hydroquebec public open data client."""

    def __init__(
        self,
        rate_code: str | None = None,
        rate_option_code: str | None = None,
        verify_ssl: bool = True,
        log_level: str | None = None,
        http_log_level: str | None = None,
        log_file: str | None = None,
        diag_folder: str | None = None,
    ):
        """Create a new Hydroquebec public data client."""
        self._hydro_client = HydroClient(
            username="",
            password="",
            verify_ssl=verify_ssl,
            log_level=http_log_level,
            diag_folder=diag_folder,
        )
        self._log_level: str | None = log_level
        self._log_file: str | None = log_file
        self._rate_code = rate_code
        self._rate_option_code = rate_option_code
        self._logger = get_logger(
            "public_client", self._log_level, log_file=self._log_file
        )
        self.peak_handler: (
            BasePeakHandler[CPCPeak] | BasePeakHandler[DPCPeak] | None
        ) = None
        if self._rate_code == "D" and self._rate_option_code == "CPC":
            self.peak_handler = CPCPeakHandler(
                "", "", "", self._hydro_client, self._logger
            )
        elif self._rate_code == "DPC":
            self.peak_handler = DPCPeakHandler(
                "", "", "", self._hydro_client, self._logger
            )

    async def check_hq_portal_status(self) -> bool:
        """Check if the Hydro Quebec website/portal is available."""
        return await self._hydro_client.check_portal_status()

    async def close_session(self) -> None:
        """Close http sessions."""
        await self._hydro_client.close_session()

    async def fetch_peak_data(self) -> None:
        """Get open peak data."""
        if self.peak_handler:
            await self.peak_handler.refresh_open_data()

    @property
    def peaks(self) -> list[CPCPeak] | list[DPCPeak]:
        """Return list of peaks."""
        if not self.peak_handler:
            return []
        return self.peak_handler.peaks

    def __repr__(self) -> str:
        """Represent object."""
        if self._rate_code and self._rate_option_code:
            return f"""<PublicClient - {self._rate_code} - {self._rate_option_code}>"""
        if self._rate_code:
            return f"""<PublicClient - {self._rate_code}>"""
        return """<PublicClient>"""
