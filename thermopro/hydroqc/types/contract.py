"""Contract json output formats."""

# pylint: disable=invalid-name
from typing import TypedDict


class ContractTyping(TypedDict, total=True):
    """Contract json output formats."""

    codeResponsabilite: str | None
    noContrat: str
    adresseConsommation: str
    idLieuConsommation: str
    noCompteContrat: str
    noInstallation: str
    noCompteur: str
    indicateurPortrait: bool
    indicateurDiagnostique: bool
    indicateurDiagnostiqueDR: bool
    documentArchivelinkID: str
    codeDiagnostique: str
    codeDiagnostiqueDR: str
    indicateurAutoReleve: bool
    indicateurMVE: bool
    adhesionMVEEncours: bool
    retraitMVEEnCours: bool
    desinscritMVE: bool
    sousConsommationMVE: bool
    surConsommationMVE: bool
    mntEcart: float
    revisionAnnuelleMVE: bool
    indicateurEligibiliteMVE: bool
    codePortrait: str
    codeAutoReleve: str
    noCivique: str
    rue: str
    appartement: str
    ville: str
    codePostal: str
    dateDebutContrat: str
    dateFinContrat: str | None
    contratAvecArriveePrevue: bool
    contratAvecArriveePrevueDansLePasse: bool
    contratAvecDepartPrevu: bool
    contratAvecDepartPrevuDansLePasse: bool
    departPrevuSansAvis: bool
    numeroTelephone: str
    posteTelephone: str
    indPuissance: bool
    codeAdhesionCPC: str
    codeEligibiliteCPC: str | None
    codeEligibiliteCLT: str | None
    tarifActuel: str
    optionTarifActuel: str
    codeEligibiliteDRCV: str
    dateDebutEligibiliteDRCV: str | None
    indEligibiliteDRCV: bool


class ListContractsTyping(TypedDict, total=True):
    """Contract list json output format."""

    listeContrats: list[ContractTyping]
