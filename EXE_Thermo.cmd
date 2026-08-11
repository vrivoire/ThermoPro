@echo off
title ThermoProScan
cls

cd C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro
call .venv\Scripts\activate.bat

@echo ----------------------------------------------------------------------------------

start "TemperatureGraph" pyinstaller -y --clean --name TemperatureGraph --onedir thermopro\TemperatureGraph.py --icon thermometer.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages --splash thermometer.png
start "EnergyGraph" pyinstaller -y --clean --name EnergyGraph --onedir thermopro\EnergyGraph.py --icon hydro-quebec.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages --splash hydro-quebec.png

nssm stop ThermoProScan
taskkill /F /T /IM ThermoProScan.exe

@echo ----------------------------------------------------------------------------------
title ThermoProScan
call pyinstaller -y --onedir thermopro\ThermoProScan.py --icon thermometer.png --nowindowed --noconsole --hidden-import win32timezone --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages

@echo ----------------------------------------------------------------------------------

nssm start ThermoProScan

rem pause
