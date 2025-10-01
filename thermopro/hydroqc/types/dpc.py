"""Hydroqc DPC types."""

# pylint: disable=invalid-name
from typing import TypedDict


class DPCDataResultsTyping(TypedDict, total=True):
    """FlexD data json sub output format."""

    dateDebut: str
    dateFin: str
    dateDernMaj: str
    hrsCritiquesAppelees: str
    hrsCritiquesAppeleesMax: str
    montantEconPerteVSTarifBase: float
    nbJoursTotauxHiver: int
    nbJoursDernMaj: int
    etatHiver: str


class DPCDataTyping(TypedDict, total=True):
    """FlexD data json output format."""

    success: bool
    results: list[DPCDataResultsTyping]


class DPCPeakDataTyping(TypedDict, total=True):
    """DPC Peak data json output format."""

    dateDebut: str
    dateFin: str


class DPCPeakListDataTyping(TypedDict, total=True):
    """DPC Peak list data json output format."""

    codeEtatPeriodeCourante: str
    dateDebutPeriode: str
    dateFinPeriode: str
    dateDerniereLecturePeriode: str
    nbJourLecturePeriode: int
    nbJourPrevuPeriode: int
    montantFacturePeriode: float
    montantProjetePeriode: float
    indContratPuissance: bool
    adresseLieuConsoPartie1: str
    adresseLieuConsoPartie2: str
    codeTarif: str
    codeOptionTarif: str | None
    listePeriodePointeCritiqueAujourdhui: None | list[DPCPeakDataTyping]
    listePeriodePointeCritiqueDemain: None | list[DPCPeakDataTyping]
