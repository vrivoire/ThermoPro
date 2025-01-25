@echo 0ff
cls
cd C:\Users\rivoi\Documents\NetBeansProjects\PycharmProjects\ThermoPro

rem pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole
start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole
start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole

rem pause
