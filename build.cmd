echo WARNING: THIS WILL OVERWRITE app.py WITH A CONVERTED VERSION OF THE .UI FILE.

set /p INPUT=Continue? [y/n]

If %INPUT%=="y" goto yes 
If %INPUT%=="n" goto no

:yes
pyuic5.exe -x .\app.ui -o app.py
exit

:no
exit
