"""HydroQC planned and not planned Outage module.

See:
    * https://www.hydroquebec.com/documents-donnees/donnees-ouvertes/pannes-interruptions.html
    * https://infopannes.solutions.hydroquebec.com/statut-adresse/
    * https://www.hydroquebec.com/data/loi-sur-acces/pdf/description-des-codes-interruption.pdf
"""

import datetime
import logging

from hydroqc import utils
from hydroqc.types import OutageCause, OutageCode, OutageStatus, OutageTyping


class Outage:
    """planned and not planned Outage class."""

    def __init__(self, raw_data: OutageTyping, logger: logging.Logger):
        """Outage constructor."""
        self._raw_data = raw_data
        self._logger = logger

    @property
    def id_(self) -> int:
        """Get outage unique ID."""
        return self._raw_data["idInterruption"]["noInterruption"]

    @property
    def start_date(self) -> datetime.datetime:
        """Get outage start date.

        Tries to use `dateDebutReport` key if exists, then falls back to `dateDebut` key.
        """
        # TODO: maybe it's more stable if we use self.status to know which
        # date we should use ?
        if (
            "dateFin" in self._raw_data
            and utils.now() > datetime.datetime.fromisoformat(self._raw_data["dateFin"])
            and "dateDebutReport" in self._raw_data
        ):
            return datetime.datetime.fromisoformat(self._raw_data["dateDebutReport"])
        return datetime.datetime.fromisoformat(self._raw_data["dateDebut"])

    @property
    def end_date(self) -> datetime.datetime | None:
        """Get outage end date.

        Tries to use `dateFinReport` key if exists, then falls back to `dateFin` key.
        """
        # TODO: maybe it's more stable if we use self.status to know which
        # date we should use ?
        if end_date_str := self._raw_data.get("dateFinEstimeeMax", ""):
            # dateFinEstimeeMax is used when the outage is currently running
            return datetime.datetime.fromisoformat(end_date_str)

        if (
            "dateFin" in self._raw_data
            and utils.now() > datetime.datetime.fromisoformat(self._raw_data["dateFin"])
            and "dateFinReport" in self._raw_data
        ):
            return datetime.datetime.fromisoformat(self._raw_data["dateFinReport"])

        if (end_date := self._raw_data.get("dateFin")) is None:
            return end_date
        return datetime.datetime.fromisoformat(end_date)

    @property
    def cause(self) -> OutageCause:
        """Get outage cause."""
        if "codeCause" not in self._raw_data:
            self._logger.warning("Outage code cause not provided. Fallback to unknown")
            return OutageCause(0)
        try:
            return OutageCause(int(self._raw_data["codeCause"]))
        except ValueError:
            self._logger.warning(
                "Outage code cause `%s` is not a supported cause code",
                self._raw_data["codeCause"],
            )
            return OutageCause(0)

    @property
    def planned_duration(self) -> datetime.timedelta:
        """Get outage duration in minutes."""
        return datetime.timedelta(minutes=self._raw_data["dureePrevu"])

    @property
    def code(self) -> OutageCode:
        """Get outage code."""
        return OutageCode(self._raw_data.get("codeIntervention", "_"))

    @property
    def status(self) -> OutageStatus:
        """Get outage status."""
        return OutageStatus(self._raw_data["etat"])

    @property
    def emergency_level(self) -> str | None:
        """Get outage status."""
        # TODO find what N and P means
        return self._raw_data.get("niveauUrgence")

    @property
    def is_planned(self) -> bool:
        """Is it a planned outage or not."""
        return self._raw_data["interruptionPlanifiee"]

    def __repr__(self) -> str:
        """Represent an outage."""
        return f"<Outage - {self.id_} - {self.start_date.isoformat()} - {self.status}>"
