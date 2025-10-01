"""Hydroquebec webuser module."""

import logging

from hydroqc.customer import Customer
from hydroqc.error import HydroQcError
from hydroqc.hydro_api.client import HydroClient
from hydroqc.logger import get_logger


class WebUser:
    """Hydroquebec webuser.

    Represents a login/password web account (Demandeur)
    """

    def __init__(
        self,
        username: str,
        password: str,
        verify_ssl: bool,
        log_level: str | None = None,
        http_log_level: str | None = None,
        log_file: str | None = None,
        diag_folder: str | None = None,
    ):
        """Create a new Hydroquebec webuser."""
        self._hydro_client = HydroClient(
            username,
            password,
            verify_ssl,
            log_level=http_log_level,
            diag_folder=diag_folder,
        )
        self._username: str = username
        self._log_level: str | None = log_level
        self.customers: list[Customer] = []
        self._logger: None | logging.Logger = None
        self._log_file: str | None = log_file

    async def check_hq_portal_status(self) -> bool:
        """Check if the Hydro Quebec website/portal is available."""
        return await self._hydro_client.check_portal_status()

    async def login(self) -> bool:
        """Login to Hydroquebec website."""
        return await self._hydro_client.login()

    @property
    def session_expired(self) -> bool:
        """Check if the session is expired."""
        return self._hydro_client.is_session_expired()

    async def get_info(self) -> None:
        """Fetch data about this webuser.

        Retrieve customers
        """
        user_info = await self._hydro_client.get_user_info()
        # We can only create the logger after getting user info at least on time
        if self._logger is None:
            self._logger = get_logger(
                f"w-{self.webuser_id}", self._log_level, log_file=self._log_file
            )

        # is the same accross contracts
        for customer_data in user_info:
            customer_names = [
                str(v)
                for k, v in customer_data.items()
                if k.startswith("nom") and k.endswith("Titulaire")
            ]
            customer_id = customer_data["noPartenaireTitulaire"]
            # Create new customer if it's not there
            if customer_id not in set(c.customer_id for c in self.customers):
                self._logger.info("Creating new customer %s", customer_id)
                customer = Customer(
                    customer_data["noPartenaireDemandeur"],
                    customer_data["noPartenaireTitulaire"],
                    customer_names,
                    self._hydro_client,
                    self._log_level,
                )
                self.customers.append(customer)
        self._logger.debug("Got webuser info")

    @property
    def webuser_id(self) -> str:
        """Get webuser id."""
        if not (data := self._hydro_client.get_token_data()):
            return ""
        return data.get("sub", "")

    @property
    def first_name(self) -> str:
        """Get webuser firstname."""
        if not (data := self._hydro_client.get_token_data()):
            return ""
        return data["given_name"]

    @property
    def last_name(self) -> str:
        """Get webuser lastname."""
        if not (data := self._hydro_client.get_token_data()):
            return ""
        return data["family_name"]

    def get_customer(self, customer_id: str) -> Customer:
        """Find customer by id."""
        if not (
            customers := [c for c in self.customers if c.customer_id == customer_id]
        ):
            raise HydroQcError(f"Customer {customer_id} not found")
        return customers[0]

    async def fetch_customers_info(self) -> None:
        """Fetch all customers info.

        It could be long if you have more than 5 customers.
        """
        if self._logger:
            self._logger.debug("Getting customers info")
        for customer in self.customers:
            await customer.get_info()
        if self._logger:
            self._logger.debug("Got customers info")

    async def close_session(self) -> None:
        """Close http sessions."""
        await self._hydro_client.close_session()

    def __repr__(self) -> str:
        """Represent object."""
        if not self.webuser_id:
            return f"""<Webuser - {self._username}>"""
        return f"""<Webuser - {self.webuser_id}>"""
