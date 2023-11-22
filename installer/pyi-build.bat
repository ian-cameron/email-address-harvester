@echo off
pyinstaller --distpath=.\..\dist --clean ^
    emailaddressharvester.spec
pause