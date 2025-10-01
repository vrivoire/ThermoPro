"""Hydroqc API Consts.

.. todo::

    avoid all the /portail/ URLs
"""

# Always get the time using HydroQuebec Local Time
REQUESTS_TIMEOUT = 30
REQUESTS_TTL = 1

HOST_LOGIN = "https://connexion.solutions.hydroquebec.com"
HOST_SESSION = "https://session.hydroquebec.com"
HOST_SERVICES = "https://services-cl.solutions.hydroquebec.com"
# HOST_SPRING = "https://cl-ec-lsw.solutions.hydroquebec.com"
HOST_RB_SOL = "https://rb.solutions.hydroquebec.com"
HOST_OUTAGES = "https://services-bs.solutions.hydroquebec.com"
HOST_OPEN_DATA = "https://donnees.solutions.hydroquebec.com"

# Azure B2C
AZB2C_TENANT_ID = "32bf9b91-0a36-4385-b231-d9a8fa3b05ab"
AZB2C_POLICY = "B2C_1A_PRD_signup_signin"
AZB2C_CLIENT_ID_WEB = "09b0ae72-6db8-4ecc-a1be-041b67afc1cd"
AZB2C_CLIENT_ID_MOBILE = "70cd7b23-de9a-4d74-8592-d378afbfb863"
AZB2C_RESPONSE_TYPE = "code"
AZB2C_SCOPE_WEB = (
    "openid https://connexionhq.onmicrosoft.com/hq-clientele/Espace.Client"
)
AZB2C_CODE_CHALLENGE_METHOD = "S256"

# Time to remove from the token expiration time to avoid calls to fail
AZB2C_TIMEOUT_SKEW_SECS = 60

# Outages
OUTAGES = f"{HOST_OUTAGES}/pan/web/api/v1/lieux-conso/etats/"
# OAUTH PATHS
AUTHORIZE_URL = (
    f"{HOST_LOGIN}/{AZB2C_TENANT_ID}/{AZB2C_POLICY.lower()}/oauth2/v2.0/authorize"
)
AUTH_URL = f"{HOST_LOGIN}/{AZB2C_TENANT_ID}/{AZB2C_POLICY}/SelfAsserted"
AUTH_CALLBACK_URL = f"{HOST_SESSION}/oauth2/callback"
TOKEN_URL = f"{HOST_LOGIN}/{AZB2C_TENANT_ID}/{AZB2C_POLICY.lower()}/oauth2/v2.0/token"

CHECK_SESSION_URL = f"{HOST_LOGIN}/hqam/oauth2/connect/checkSession"


SECURITY_URL = f"{HOST_SESSION}/config/security.json"
SESSION_REFRESH_URL = f"{HOST_SESSION}/oauth2/callback/silent-refresh"
LOGIN_URL_6 = f"{HOST_SERVICES}/wsapi/web/prive/api/v3_0/conversion/codeAcces"

# OPEN DATA PEAK URL
OPEN_DATA_PEAK_URL = (
    f"{HOST_OPEN_DATA}/donnees-ouvertes/data/json/pointeshivernales.json"
)

# Initialization uri
RELATION_URL = f"{HOST_SERVICES}/wsapi/web/prive/api/v1_0/relations"

FLEXD_DATA_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesMoisHiverFlex"
)
FLEXD_PEAK_URL = f"{HOST_SERVICES}/conso/portraitweb/api/v3_0/conso"
CONSO_CSV_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceTelechargerDonneesConsommation"
)
CONSO_OVERVIEW_CSV_URL = (
    f"{HOST_SERVICES}/lsw/portail/en/group/clientele/portrait-de-consommation/"
    "resourceTelechargerPeriodesFacturation"
)

# TODO avoid all the /portail/ URLs
SESSION_URL = f"{HOST_SERVICES}/lsw/portail/prive/maj-session/"
# TODO avoid all the /portail/ URLs
CONTRACT_HTML_URL = f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/gerer-mon-compte"
#
INFOBASE_URL = f"{HOST_SERVICES}/wsapi/web/prive/api/v3_0/partenaires/infoBase"
CONTRACT_SUMMARY_URL = (
    f"{HOST_SERVICES}/wsapi/web/prive/api/v3_0/partenaires/"
    "calculerSommaireContractuel?indMAJNombres=true"
)
CONTRACT_LIST_URL = f"{HOST_SERVICES}/wsapi/web/prive/api/v3_0/partenaires/contrats"

CUSTOMER_INFO_URL = f"{HOST_SERVICES}/wsapi/web/prive/api/v3_0/partenaires/infoCompte"

# TODO avoid all the /portail/ URLs
PORTRAIT_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation"
)
# TODO avoid all the /portail/ URLs
PERIOD_DATA_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesPeriodesConsommation"
)

# TODO avoid all the /portail/ URLs
ANNUAL_DATA_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesConsommationAnnuelles"
)

# TODO avoid all the /portail/ URLs
MONTHLY_DATA_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesConsommationMensuelles"
)

# TODO avoid all the /portail/ URLs
DAILY_CONSUMPTION_API_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesQuotidiennesConsommation"
)

# TODO avoid all the /portail/ URLs
HOURLY_CONSUMPTION_API_URL = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesConsommationHoraires"
)
# TODO avoid all the /portail/ URLs
HOURLY_DATA_URL_2 = (
    f"{HOST_SERVICES}/lsw/portail/fr/group/clientele/portrait-de-consommation/"
    "resourceObtenirDonneesMeteoHoraires"  # not used
)

# CPC
GET_CPC_API_URL = (
    f"{HOST_SERVICES}/wsapi/web/prive/api/v3_0/tarificationDynamique/"
    "creditPointeCritique"
)
# IS PORTAL RUNNING
IS_HYDRO_PORTAL_UP_URL = f"{HOST_SESSION}/portail/fr/group/clientele/gerer-mon-compte"
