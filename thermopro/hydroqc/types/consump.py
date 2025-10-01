"""Hydroqc custom types."""

# pylint: disable=invalid-name
from typing import TypedDict


# API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
# portrait-de-consommation/resourceObtenirDonneesConsommationHoraires
class ConsumpHourlyResultTyping(TypedDict, total=True):
    """Consumption Hourly json sub output format."""

    heure: "str"
    consoReg: float
    consoHaut: float
    consoTotal: float
    codeConso: str
    codeEvemenentEnergie: str
    zoneMessageHTMLEnergie: str | None


class ConsumpHourlyResultsTyping(TypedDict, total=True):
    """Consumption Hourly json sub output format."""

    codeTarif: str
    affichageTarifFlex: bool
    dateJour: str
    echelleMinKwhHeureParJour: int
    echelleMaxKwhHeureParJour: int
    zoneMsgHTMLNonDispEnergie: str | None
    zoneMsgHTMLNonDispPuissance: str | None
    indErreurJourneeEnergie: bool
    indErreurJourneePuissance: bool
    listeDonneesConsoEnergieHoraire: list[ConsumpHourlyResultTyping]


class ConsumpHourlyTyping(TypedDict, total=True):
    """Consumption Hourly json output format."""

    success: bool
    results: ConsumpHourlyResultsTyping


# API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
# portrait-de-consommation/resourceObtenirDonneesQuotidiennesConsommation
class ConsumpDailyResultTyping(TypedDict, total=True):
    """Consumption Daily json sub output format."""

    dateJourConso: str
    zoneMessageHTMLQuot: str | None
    consoRegQuot: float
    consoHautQuot: float
    consoTotalQuot: float
    codeConsoQuot: str
    tempMoyenneQuot: int
    codeTarifQuot: str
    affichageTarifFlexQuot: bool
    codeEvenementQuot: str


class ConsumpDailyResultsTyping(TypedDict, total=True):
    """Consumption Daily json sub output format."""

    courant: ConsumpDailyResultTyping
    compare: ConsumpDailyResultTyping


class ConsumpDailyTyping(TypedDict, total=True):
    """Consumption Daily json output format."""

    success: bool
    results: list[ConsumpDailyResultsTyping]


# API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
# portrait-de-consommation/resourceObtenirDonneesConsommationMensuelles
class ConsumpMonthlyResultTyping(TypedDict, total=True):
    """Consumption Monthly json sub output format."""

    dateDebutMois: str
    dateFinMois: str
    codeConsoMois: str
    nbJourCalendrierMois: int
    presenceTarifDTmois: bool
    tempMoyenneMois: int
    moyenneKwhJourMois: float
    affichageTarifFlexMois: bool
    consoRegMois: int
    consoHautMois: int
    consoTotalMois: int
    zoneMessageHTMLMois: str | None
    indPresenceCodeEvenementMois: bool


class ConsumpMonthlyResultsTyping(TypedDict, total=True):
    """Consumption Monthly json sub output format."""

    courant: ConsumpMonthlyResultTyping
    compare: ConsumpMonthlyResultTyping


class ConsumpMonthlyTyping(TypedDict, total=True):
    """Consumption Monthly json output format."""

    success: bool
    results: list[ConsumpMonthlyResultsTyping]


# API URL: https://cl-ec-spring.hydroquebec.com/portail/fr/group/clientele/
# portrait-de-consommation/resourceObtenirDonneesConsommationAnnuelles
class ConsumpAnnualCompareTyping(TypedDict, total=True):
    """Consumption Annual json sub output format."""

    dateDebutAnnee: str
    dateFinAnnee: str
    nbJourCalendrierAnnee: int
    moyenneKwhJourAnnee: float
    consoRegAnnee: int
    consoHautAnnee: int
    consoTotalAnnee: int
    montantFactureAnnee: float
    moyenneDollarsJourAnnee: float
    isEligibleDRCV: bool
    codeTarifAnnee: str
    montantGainPerteDTversusBaseAnnee: float
    montantChauffageAnnee: int
    montantClimatisationAnnee: int
    kwhChauffageAnnee: int
    kwhClimatisationAnnee: int
    coutCentkWh: float


class ConsumpAnnualCurrentTyping(ConsumpAnnualCompareTyping, total=True):
    """Consumption Annual json sub output format."""

    zoneMsgHTMLAnneeSuiviDT: str
    texteValeurChauffage: str | None
    texteValeurClimatisation: str | None
    tooltipIdChauffage: str
    tooltipIdClimatisation: str
    tooltipIdChauffageComparaison: str
    tooltipIdClimatisationComparaison: str


class ConsumpAnnualResultsTyping(TypedDict, total=True):
    """Consumption Annual json sub output format."""

    courant: ConsumpAnnualCurrentTyping
    compare: ConsumpAnnualCompareTyping


class ConsumpAnnualTyping(TypedDict, total=True):
    """Consumption Annual json output format."""

    success: bool
    results: list[ConsumpAnnualResultsTyping]


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


DTDataResultsTyping = DPCDataResultsTyping


class DTDataTyping(TypedDict, total=True):
    """FlexD data json output format."""

    success: bool
    results: list[DTDataResultsTyping]


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
