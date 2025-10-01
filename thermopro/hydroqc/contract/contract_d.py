"""Hydroquebec contract module."""

from hydroqc.contract.contract_residential import ContractResidential
from hydroqc.hydro_api.client import HydroClient


class ContractD(ContractResidential):
    """Hydroquebec contract.

    Represents a contract (contrat)
    """

    _rate_code = "D"
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
