import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

from ThermoProScan import ThermoProScan


class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "ThermoProScan"
    _svc_display_name_ = "ThermoProScan"
    thermoProScan: ThermoProScan = ThermoProScan()

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        AppServerSvc.thermoProScan.stop(AppServerSvc.thermoProScan)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        AppServerSvc.thermoProScan.start(AppServerSvc.thermoProScan)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
