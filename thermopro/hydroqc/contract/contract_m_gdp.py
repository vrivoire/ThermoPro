"""Hydroquebec contract module."""

from hydroqc.contract.contract_m import ContractM
from hydroqc.hydro_api.client import HydroClient


class ContractMGDP(ContractM):
    """Hydroquebec contract.

    Represents a contract (contrat)
    """

    _rate_option_code = "GDP"

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
        ContractM.__init__(
            self,
            applicant_id,
            customer_id,
            account_id,
            contract_id,
            hydro_client,
            log_level,
        )
