"""HydroQc Error Module."""


class HydroQcError(Exception):
    """Base HydroQc Error."""


class HydroQcHTTPError(HydroQcError):
    """HTTP HydroQc Error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize."""
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class HydroQcAnnualError(HydroQcError):
    """Annual HydroQc Error."""


class HydroQcCPCPeakError(HydroQcError):
    """CPC peak HydroQc Error."""


class HydroQcDPCPeakError(HydroQcError):
    """DPC peak HydroQc Error."""
