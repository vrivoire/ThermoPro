@echo 0ff
cls
cd C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro

rem pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole
start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro
start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.png --nowindowed --noconsole --paths C:\Users\adele\Documents\NetBeansProjects\PycharmProjects\ThermoPro

rem pause
