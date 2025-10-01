"""Hydroqc custom types."""

from hydroqc.types.account import (
    AccountContractSummaryTyping,
    AccountTyping,
    InfoAccountTyping,
    ListAccountsContractsTyping,
)
from hydroqc.types.common import (
    IDTokenTyping,
    OpenDataPeakEvent,
    OpenDataPeakEventOffer,
    Rates,
)
from hydroqc.types.consump import (
    ConsumpAnnualTyping,
    ConsumpDailyTyping,
    ConsumpHourlyTyping,
    ConsumpMonthlyTyping,
    DPCDataTyping,
    DPCPeakDataTyping,
    DPCPeakListDataTyping,
    DTDataTyping,
)
from hydroqc.types.contract import ContractTyping, ListContractsTyping
from hydroqc.types.cpc import CPCDataTyping, CriticalPeakDataTyping, PeriodDataTyping
from hydroqc.types.outage import (
    OutageCause,
    OutageCode,
    OutageListTyping,
    OutageStatus,
    OutageTyping,
)

__all__ = [
    "InfoAccountTyping",
    "ConsumpHourlyTyping",
    "ConsumpDailyTyping",
    "ConsumpMonthlyTyping",
    "ConsumpAnnualTyping",
    "CriticalPeakDataTyping",
    "PeriodDataTyping",
    "CPCDataTyping",
    "ListAccountsContractsTyping",
    "ContractTyping",
    "AccountTyping",
    "IDTokenTyping",
    "AccountContractSummaryTyping",
    "ListContractsTyping",
    "DPCDataTyping",
    "DTDataTyping",
    "DPCPeakListDataTyping",
    "DPCPeakDataTyping",
    "OutageListTyping",
    "OutageTyping",
    "OutageCause",
    "OutageStatus",
    "OutageCode",
    "Rates",
    "OpenDataPeakEventOffer",
    "OpenDataPeakEvent",
]
