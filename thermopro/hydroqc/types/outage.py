"""Outage output formats."""

# pylint: disable=invalid-name
from enum import Enum, IntEnum
from typing import TypedDict

# Outages

# Outage example
# [{"idLieuConso":"0500314629","etat":"N","date":"2023-01-04T03:25:40.000+00:00",
#   "interruptions":[{
#       "idInterruption":{"site":"ORL","typeObjet":"I","noInterruption":37224,"noSection":1},
#       "dateDebut":"2023-01-04T03:25:40.000+00:00",
#       "etat":"C",
#       "dateFinEstimeeMax":"2023-01-04T04:30:00.000+00:00",
#       "codeIntervention":"L","niveauUrgence":"P","nbClient":3,"codeCause":"51",
#       "codeMunicipal":"5557",
#       "datePublication":"2023-01-04T03:25:54.932+00:00","codeRemarque":"","dureePrevu":0,
#       "probabilite":0.0,"interruptionPlanifiee":false}]}]

# Planned outage example
# {'idLieuConso': '0502451550', 'etat': 'A', 'date': '2022-06-28T09:14:00.000+00:00',
#  'interruptions': [{
#       'idInterruption': {'site': 'LAV', 'typeObjet': 'A',
#                          'noInterruption': 117915, 'noSection': 1},
#       'dateDebut': '2022-12-21T13:30:00.000+00:00',
#       'dateFin': '2022-12-21T20:30:00.000+00:00',
#       'dateDebutReport': '2023-01-12T13:30:00.000+00:00',
#       'dateFinReport': '2023-01-12T20:30:00.000+00:00',
#       'etat': 'R', 'nbClient': 18, 'codeCause': '62', 'codeMunicipal': '9160',
#       'datePublication': '2022-12-20T16:02:52.920+00:00',
#       'codeRemarque': '91', 'dureePrevu': 420, 'probabilite': 0.0, 'interruptionPlanifiee': True
# }]}

# No outage example
# [{'idLieuConso': '0501706180', 'etat': 'A',
# 'date': '2022-10-20T19:50:13.000+00:00', 'interruptions': []}]


class OutageCause(IntEnum):
    """Outage cause enum."""

    # Unkonwn (not official HQ code)
    inconnu = 0
    # Not planned
    defaillance = 11
    surcharge = 12
    montage = 13
    protection = 14
    non_qualite = 15
    foudre = 21
    precipitation = 22
    sinistre_naturel = 24
    vent = 25
    temperature_extreme = 26
    subtance_sel = 31
    pollution_industriel = 32
    vetuste = 33
    incendie_fuite_de_gaz = 34
    erreur_de_manoeuvre = 41
    contact_accidentel = 42
    essai = 43
    man_sec_non_plan = 44
    vegetation = 51
    oiseau = 52
    animal = 53
    vehicule = 54
    objet = 55
    vandalisme = 56
    equipement_client = 57
    indetermine = 58
    non_fournie = 59
    # Planned
    entretien = 61
    modification_reseau = 62
    travaux_securitaire = 63
    manoeuvre_securitaire = 64
    manoeuvre = 65
    securite_public = 66
    interruption_demande_client = 76
    reforcement_de_reseau = 68
    programme_special = 69
    travaux_vegetation = 77


# TODO use strEnum on python 3.11
class OutageCode(Enum):
    """Outage code enum."""

    # Unkonwn (not official HQ code)
    inconnu = "_"
    travaux_assignes = "A"
    travaux_en_cours = "L"
    equipe_en_route = "R"
    en_analyse = "N"


class OutageStatus(Enum):
    """Outage Status enum."""

    planifie_confirme = "P"
    courante_confirme = "C"
    planifie_reporte = "R"
    termine = "T"
    non_confirme = "N"
    annule = "A"


class OutageIdTyping(TypedDict, total=True):
    """Outage id json output format."""

    site: str
    typeObjet: str
    noInterruption: int
    noSection: int


class OutageTyping(TypedDict, total=True):
    """Outage json output format."""

    idInterruption: OutageIdTyping
    dateDebut: str
    dateFin: str
    dateDebutReport: str
    dateFinReport: str
    dateFinEstimeeMax: str
    etat: OutageStatus
    nbClient: int
    codeCause: OutageCause
    codeIntervention: OutageCode | None
    codeMunicipal: str
    datePublication: str
    codeRemarque: str
    dureePrevu: int  # minutes
    probabilite: float  # 0.0
    interruptionPlanifiee: bool
    niveauUrgence: str | None


class OutageListTyping(TypedDict, total=True):
    """Outage list json output format."""

    idLieuConso: str
    etat: str
    date: str
    interruptions: list[OutageTyping]
