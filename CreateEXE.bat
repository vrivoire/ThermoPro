@echo 0ff
cls
cd C:\Users\rivoi\Documents\NetBeansProjects\PycharmProjects\ThermoPro

rem pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole
pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

pause
