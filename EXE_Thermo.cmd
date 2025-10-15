@echo 0ff
title ThermoProScan
cls

cd C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro
call .venv\Scripts\activate.bat
pip freeze > requirements.txt

start "ThermoProGraph" pyinstaller -y --onedir thermopro\ThermoProGraph.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages

taskkill /F /T /IM ThermoProScan.exe

call pyinstaller -y --onedir thermopro\ThermoProScan.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro;C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro\thermopro;C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\.venv\Lib\site-packages

start C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\dist\ThermoProScan\ThermoProScan.exe

rem pause
