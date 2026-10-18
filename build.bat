@echo off
rem Builds dist\RicamoFacile.exe (a single file you can copy to any Windows 10/11 PC).
python -m pip install -r requirements-dev.txt || goto :error
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name RicamoFacile ^
  --icon assets\icon.ico ^
  --add-data "ricamo_facile\data;ricamo_facile\data" ^
  --exclude-module pytest ^
  RicamoFacile.pyw || goto :error
echo.
echo Fatto! / Done!  -^>  dist\RicamoFacile.exe
goto :eof
:error
echo Errore durante la creazione dell'eseguibile. / Build failed.
exit /b 1
