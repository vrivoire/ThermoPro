"""Hydroquebec customer module."""

import logging

from hydroqc import contract as contractModule
from hydroqc.account import Account
from hydroqc.error import HydroQcError
from hydroqc.hydro_api.client import HydroClient
from hydroqc.logger import get_logger


class Customer:
    """Hydroquebec customer.

    Represents one customer (Titulaire)
    """

    def __init__(
        self,
        applicant_id: str,
        customer_id: str,
        customer_names: list[str],
        hydro_client: HydroClient,
        log_level: str | None = None,
    ):
        """Create a new customer."""
        self._logger: logging.Logger = get_logger(
            f"c-{customer_id}", log_level, parent=f"w-{applicant_id}"
        )
        self._log_level: str | None = log_level
        self._no_partenaire_demandeur: str = applicant_id
        self._no_partenaire_titulaire: str = customer_id
        self._nom_titulaires: list[str] = customer_names
        self._hydro_client: HydroClient = hydro_client
        self.accounts: list[Account] = []
        self._firstname: str = ""
        self._lastname: str = ""
        self._language: str = ""
        self._id_technique: str = ""
        self._infocompte_enabled: bool | None = None

    async def get_info(self) -> None:
        """Retrieve account id, customer id and contract id."""
        self._logger.debug("Getting customer info")
        customer_data = await self._hydro_client.get_customer_info(
            self.applicant_id, self.customer_id
        )
        self._infocompte_enabled = customer_data["indEligibilite"]
        if self.infocompte_enabled:
            if not customer_data["infoCockpitPourPartenaireModel"]:
                return
            self._firstname = customer_data["infoCockpitPourPartenaireModel"]["prenom"]
            self._lastname = customer_data["infoCockpitPourPartenaireModel"]["nom"]
            self._email = customer_data["infoCockpitPourPartenaireModel"]["courriel"]
            self._language = customer_data["infoCockpitPourPartenaireModel"][
                "langueCorrespondance"
            ]
            self._id_technique = customer_data["infoCockpitPourPartenaireModel"][
                "idTechnique"
            ]

        # Get the customer account_contract list
        raw_account_list = await self._hydro_client.list_account_contract(
            self.applicant_id, self.customer_id
        )
        for raw_account_data in raw_account_list["comptesContrats"]:
            account_id = raw_account_data["noCompteContrat"]
            # Create new account if it's not there
            if account_id not in [a.account_id for a in self.accounts]:
                self._logger.info("Creating new account %s", account_id)
                account = Account(
                    self.applicant_id,
                    self.customer_id,
                    account_id,
                    [],
                    self._hydro_client,
                    self._log_level,
                )
                self.accounts.append(account)
            else:
                account = [a for a in self.accounts if a.account_id == account_id][0]
            if self.infocompte_enabled:
                # TODO find a way to get account info when infocompte is not available
                await account.get_info()

            for contract_id in raw_account_data["listeNoContrat"]:
                if contract_id not in [c.contract_id for c in account.contracts]:
                    contract_info = await account.get_contract_info(contract_id)
                    self._logger.info("Creating new contracts %s", contract_id)
                    rate = contract_info["tarifActuel"]
                    rate_option = contract_info.get("optionTarifActuel", "")
                    contract_class_name = f"Contract{rate}{rate_option}"
                    if not hasattr(contractModule, contract_class_name):
                        self._logger.warning(
                            f"Contract {contract_id} for account.account_id for "
                            f"customer {account.customer_id} has rate `{rate}` "
                            f"with option `{rate_option}` "
                            "is not supported, falling back to Fallback Contract. "
                            "This contract has basic features and could crash anytime. "
                            "Please open an issue to support it."
                        )
                        contract_class_name = "ContractFallBack"
                    contract = getattr(contractModule, contract_class_name)(
                        self.applicant_id,
                        self.customer_id,
                        account_id,
                        contract_id,
                        self._hydro_client,
                        self._log_level,
                    )
                    account.contracts.append(contract)
                else:
                    contract = [
                        c for c in account.contracts if c.contract_id == contract_id
                    ][0]
                await contract.get_info()
        self._logger.debug("Got customer info")

    @property
    def applicant_id(self) -> str:
        """Get applicant id."""
        return self._no_partenaire_demandeur

    @property
    def customer_id(self) -> str:
        """Get customer id."""
        return self._no_partenaire_titulaire

    @property
    def names(self) -> list[str]:
        """Could be ["firstname", "lastname"] or ["fullname1", "fullname2"]."""
        return self._nom_titulaires

    @property
    def infocompte_enabled(self) -> bool | None:
        """Is the infocompte page available or not for this customer/account."""
        return self._infocompte_enabled

    def get_account(self, account_id: str) -> Account:
        """Find account by id."""
        if not (accounts := [c for c in self.accounts if c.account_id == account_id]):
            raise HydroQcError(f"Account {account_id} not found")
        return accounts[0]

    def __repr__(self) -> str:
        """Represent object."""
        return f"""<Customer - {self.applicant_id} - {self.customer_id}>"""
