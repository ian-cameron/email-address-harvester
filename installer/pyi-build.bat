@echo off
pyinstaller --distpath=.\..\dist --clean ^
    emailaddressharvester.spec
echo "Done!"
pause