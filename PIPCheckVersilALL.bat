rem @echo off
echo --------------------------------- All ---------------------------------

echo .
call C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\PoidsPression\PIPCheckVersionPoidsPression.bat
echo .
call C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\PIPCheckVersionThermoPro.bat
echo .
powershell "start \"cmd\" \"/C call C:\Users\ADELE\Documents\NetBeansProjects\PycharmProjects\ThermoPro\PIPCheckVersionRoot.bat\" -v runAs"

pause