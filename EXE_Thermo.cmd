@echo 0ff
cls

cd C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro

start pyinstaller -y --onedir thermopro\ThermoProGraph.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro

taskkill /F /IM ThermoProScan.exe

call pyinstaller -y --onedir thermopro\ThermoProScan.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro

start C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\dist\ThermoProScan\ThermoProScan.exe



rem pause
