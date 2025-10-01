"""Hydroquebec contract module."""

from hydroqc.contract.common import check_annual_data_present, check_period_data_present
from hydroqc.contract.contract_residential import ContractResidential
from hydroqc.hydro_api.client import HydroClient


class ContractDT(ContractResidential):
    """Hydroquebec contract.

    Represents a contract (contrat)
    """

    _rate_code = "DT"
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
        ContractResidential.__init__(
            self,
            applicant_id,
            customer_id,
            account_id,
            contract_id,
            hydro_client,
            log_level,
        )

    @property
    @check_period_data_present
    def cp_lower_price_consumption(self) -> float:
        """Total lower priced consumption since the current period started."""
        return self._all_period_data[0]["consoRegPeriode"]

    @property
    @check_period_data_present
    def cp_higher_price_consumption(self) -> float:
        """Total higher priced consumption since the current period started."""
        return self._all_period_data[0]["consoHautPeriode"]

    @property
    @check_annual_data_present
    def amount_saved_vs_base_rate(self) -> float:
        """Annual money saved vs D base rate."""
        return self._annual_info_data["results"][0]["courant"][
            "montantGainPerteDTversusBaseAnnee"
        ]
