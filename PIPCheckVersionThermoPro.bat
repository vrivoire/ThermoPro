@echo off
echo --------------------------------- ThermoPro ---------------------------------

cd %USERPROFILE%\Documents\NetBeansProjects\PycharmProjects\ThermoPro
echo .
call .venv\Scripts\activate.bat
echo .
pip list -v
rem echo .
rem pip-review
echo .
pip-review --interactive
echo .
pip list
echo .
pip freeze > requirements.txt
echo .
pause