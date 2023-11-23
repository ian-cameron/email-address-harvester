from distutils.core import setup
import py2exe, sys, os
sys.argv.append('py2exe')
setup(
    options = {'py2exe': {'bundle_files': 1, 'compressed': True, 'dist_dir': ".\\..\\dist"}},
    console = [{'script': ".\\..\\src\\emailaddressharvester.py", "icon_resources": [(1, ".\\assets\\icon.ico")]}],
    zipfile = None,
)