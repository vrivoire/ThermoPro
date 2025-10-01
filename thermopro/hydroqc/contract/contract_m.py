"""Hydroquebec contract module."""

from collections.abc import Iterator
from datetime import date
from io import StringIO

from hydroqc.contract.common import Contract
from hydroqc.hydro_api.client import HydroClient


class ContractM(Contract):
    """Hydroquebec contract.

    Represents a contract (contrat)
    """

    _rate_code = "M"
    _rate_option_code = ""

    def __init__(
        self,
        applicant_id: str,
        customer_id: str,
        account_id: str,
        contract_id: str,
        hydro_client: HydroClient,
        log_level: str | None = None,
    ):
        """Create a new Hydroquebec contract."""
        Contract.__init__(
            self,
            applicant_id,
            customer_id,
            account_id,
            contract_id,
            hydro_client,
            log_level,
        )

    async def get_power_demand_per_15min(
        self,
        start_date: date,
        end_date: date,
        raw_output: bool = False,
    ) -> Iterator[list[str | int | float]] | StringIO:
        """Get power demand per 15 min on a specific date range."""
        data_csv = await self._hydro_client.get_consumption_csv(
            self.applicant_id,
            self.customer_id,
            self.contract_id,
            start_date,
            end_date,
            "puissance-min",
            raw_output,
        )
        return data_csv

    async def get_daily_energy_and_power(
        self,
        start_date: date,
        end_date: date,
        raw_output: bool = False,
    ) -> Iterator[list[str | int | float]] | StringIO:
        """Get daily energy and power data on a specific date range."""
        data_csv = await self._hydro_client.get_consumption_csv(
            self.applicant_id,
            self.customer_id,
            self.contract_id,
            start_date,
            end_date,
            "puissance-jour",
            raw_output,
        )
        return data_csv
