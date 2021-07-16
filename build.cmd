@echo off

set compileUI=0
set build=0

FOR %%A IN (%*) DO (
    IF "%%A"=="-compileUI" set compileUI=1
    IF "%%A"=="-build" set build=1
)

if %compileUI%==1 pyuic5.exe -x .\ui\mainwin.ui -o mainwin.py

if %build%==1 pyinstaller --onefile --windowed --icon=favicon.ico app.py 

exit