"""Hydroquebec Account Module."""

from hydroqc.contract.common import Contract
from hydroqc.error import HydroQcError
from hydroqc.hydro_api.client import HydroClient
from hydroqc.logger import get_logger
from hydroqc.types import ContractTyping, ListAccountsContractsTyping


class Account:
    """Hydroquebec account.

    Represents an account (compte)
    """

    _balance: float
    _balance_unpaid: float
    _last_bill: float

    def __init__(
        self,
        applicant_id: str,
        customer_id: str,
        account_id: str,
        contracts: list[Contract],
        hydro_client: HydroClient,
        log_level: str | None = None,
    ):
        """Create an Hydroquebec account."""
        self._logger = get_logger(
            f"a-{account_id}", log_level, parent=f"w-{applicant_id}.c-{customer_id}"
        )
        self._no_partenaire_demandeur: str = applicant_id
        self._no_partenaire_titulaire: str = customer_id
        self._no_compte_contrat: str = account_id
        self._hydro_client: HydroClient = hydro_client
        self.contracts: list[Contract] = contracts
        self._address: str = ""
        self._bill_date_create: str = ""
        self._bill_date_due: str = ""
        self._bill_date_next: str = ""

    @property
    def applicant_id(self) -> str:
        """Get applicant id."""
        return self._no_partenaire_demandeur

    @property
    def customer_id(self) -> str:
        """Get customer id."""
        return self._no_partenaire_titulaire

    @property
    def account_id(self) -> str:
        """Get account id."""
        return self._no_compte_contrat

    async def get_info(self) -> ListAccountsContractsTyping:
        """Fetch latest data of this account."""
        self._logger.debug("Getting account info")
        data = await self._hydro_client.get_account_info(
            self.applicant_id, self.customer_id, self.account_id
        )
        self._address = data["adresse"].strip()
        self._balance = data["solde"]
        self._balance_unpaid = data["solde"]
        self._last_bill = data["montant"]
        self._bill_date_create = data["dateEmission"]
        self._bill_date_due = data["dateEcheance"]
        self._bill_date_next = data["dateProchaineFacture"]
        self._logger.debug("Got account info")
        return data

    @property
    def balance(self) -> float:
        """Get current balance."""
        return self._balance

    async def get_contract_info(self, contract_id: str) -> ContractTyping:
        """Fetch info about a contract."""
        self._logger.info("Get contract info")
        _raw_info_data = await self._hydro_client.get_contract_info(
            self.applicant_id, self.customer_id, self.account_id, contract_id
        )
        return _raw_info_data

    def get_contract(self, contract_id: str) -> Contract:
        """Find contract by id."""
        if not (
            contracts := [c for c in self.contracts if c.contract_id == contract_id]
        ):
            raise HydroQcError(
                f"Contract {contract_id} not found for account {self.account_id} "
                f"for customer {self.customer_id}"
            )
        return contracts[0]

    def __repr__(self) -> str:
        """Represent object."""
        return f"""<Account - {self.applicant_id} - {self.customer_id} - {self.account_id}>"""
