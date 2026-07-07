@echo off
echo.
echo  Building Henriquix20 Encoder...
echo.

python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name "Henriquix20 Encoder" ^
  --icon "logo.ico" ^
  --add-data "logo.png;." ^
  --add-data "logo.ico;." ^
  --collect-all "customtkinter" ^
  --collect-all "tkinterdnd2" ^
  --hidden-import "PIL" ^
  --hidden-import "PIL.Image" ^
  --hidden-import "urllib.request" ^
  --hidden-import "urllib.error" ^
  main.py

echo.
echo  Done! Check the dist folder.
echo.
pause