@echo off
setlocal enabledelayedexpansion
rem Simple packager for the Qt app. Prefers uv if present, otherwise uses python -m pip.

set "ROOT=%~dp0"
pushd "%ROOT%"

where uv >nul 2>nul
if %errorlevel%==0 (
  set "INSTALL=uv pip install"
  set "PYTHON=python"
) else (
  where python3 >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON=python3"
  ) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
      set "PYTHON=python"
    ) else (
      echo Python not found in PATH.>&2
      exit /b 1
    )
  )
  set "INSTALL=%PYTHON% -m pip install"
)

%INSTALL% --upgrade pyinstaller || exit /b 1

%PYTHON% -m PyInstaller --noconfirm --windowed --clean ^
  --name Assemblitor ^
  --add-data "program;program" ^
  --add-data "profile;profile" ^
  --add-data "fonts;fonts" ^
  Assemblitor.pyw

popd
echo.
echo Build complete. Binaries are in dist\Assemblitor\
