@echo off
echo --------------------------------- ThermoPro ---------------------------------

cd %USERPROFILE%\Documents\NetBeansProjects\PycharmProjects\ThermoPro
echo .
call .venv\Scripts\activate.bat
echo .
pip list -v
echo .
pip-review
echo .
pip-review --interactive
echo .
pip list
echo .
pip freeze > requirements.txt
echo .
pause