# Build Standalone Executable
## Prereqs

* Activate a python environment (tested with 3.11) 
* Install `/requirements.txt`
* Confirm deps are installed by running `python /src/emailaddressharvester.py`

## PyInstaller (Preferred)

* Install `/installer/pyi-requirements.txt`
* Run pyi-build.bat
* Windows executable is saved in ./../dist folder

## Py2Exe (Fallback)

* Install `/installer/p2e-requirements.txt`
* Run p2e-build.bat
* Windows executable is saved in ./../dist folder
