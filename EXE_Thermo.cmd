@echo off
title ThermoProScan
cls

cd C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro
call .venv\Scripts\activate.bat

@echo ----------------------------------------------------------------------------------

start "ThermoProGraph" pyinstaller -y --onedir thermopro\ThermoProGraph.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages

nssm stop ThermoProScan
taskkill /F /T /IM ThermoProScan.exe

@echo ----------------------------------------------------------------------------------

call pyinstaller -y --onedir thermopro\ThermoProScan.py --icon=ThermoPro.png --nowindowed --noconsole --hidden-import win32timezone --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages

@echo ----------------------------------------------------------------------------------

nssm start ThermoProScan

rem pause
