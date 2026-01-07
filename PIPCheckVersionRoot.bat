@echo off
echo --------------------------------- Root ---------------------------------

cd %USERPROFILE%\Documents\NetBeansProjects\PycharmProjects
echo .
pip list -v
echo .
pip-review --interactive
echo .
pip list
echo .
pip freeze > requirements.txt
echo .
pause