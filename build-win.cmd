@echo off
rem A simple windows build script for the Squad Mortar Toolkit. Requires PyInstaller
pyinstaller --clean --noconsole -n fdc -F fdc.py
pyinstaller --clean --noconsole -n mc -F mc.py
pyinstaller --clean --noconsole -n smc -F smc.py
rmdir /S /Q build
rmdir /S /Q __pycache__
del *.spec
pause
