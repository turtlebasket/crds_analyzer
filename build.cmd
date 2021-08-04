@echo off

set compileUI=0
set build=0

IF "%~1" == "" (
	echo --------------
	echo  BUILD SCRIPT 
	echo --------------
	echo -compileUI	Generate main window class from .UI file
	echo -build		Build standalone desktop app with embedded python runtime
	exit
)

FOR %%A IN (%*) DO (
    IF "%%A"=="-compileUI" set compileUI=1
    IF "%%A"=="-build" set build=1
)

if %compileUI%==1 (
	pyuic5.exe -x .\ui\mainwin.ui -o mainwin.py
	if %ERRORLEVEL% EQU 0 echo Generated mainwin.py.
	if %ERRORLEVEL% EQU 1 echo Generation failed. 
)

if %build%==1 pyinstaller --onefile --windowed --icon=favicon.ico app.py 

exit
