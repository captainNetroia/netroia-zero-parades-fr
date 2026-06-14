@echo off
chcp 65001 >nul
title Zero Parades — Installation Traduction Française
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   ZERO PARADES — Traduction Française 1.0   ║
echo  ║   Fan Translation par NetroIA               ║
echo  ║   netroia.tech                              ║
echo  ╚══════════════════════════════════════════════╝
echo.

set "BUNDLE_NAME=g5ibkj7vdwf2g67g_assets_all_b66647f505c41665a95bd1ec7b62de70.bundle"
set "BUNDLE_SUBPATH=ZeroParades_Data\StreamingAssets\aa\StandaloneWindows64"
set "GAME_FOLDER=ZERO PARADES For Dead Spies"
set "GAME_PATH="

echo [1/4] Recherche du jeu sur vos disques...

for %%d in (C D E F G H) do (
    if exist "%%d:\Program Files (x86)\Steam\steamapps\common\%GAME_FOLDER%\%BUNDLE_SUBPATH%\%BUNDLE_NAME%" (
        set "GAME_PATH=%%d:\Program Files (x86)\Steam\steamapps\common\%GAME_FOLDER%\%BUNDLE_SUBPATH%"
    )
    if exist "%%d:\SteamLibrary\steamapps\common\%GAME_FOLDER%\%BUNDLE_SUBPATH%\%BUNDLE_NAME%" (
        set "GAME_PATH=%%d:\SteamLibrary\steamapps\common\%GAME_FOLDER%\%BUNDLE_SUBPATH%"
    )
    if exist "%%d:\Steam\steamapps\common\%GAME_FOLDER%\%BUNDLE_SUBPATH%\%BUNDLE_NAME%" (
        set "GAME_PATH=%%d:\Steam\steamapps\common\%GAME_FOLDER%\%BUNDLE_SUBPATH%"
    )
)

if "%GAME_PATH%"=="" (
    echo.
    echo  [!] Dossier du jeu non trouvé automatiquement.
    echo.
    echo  Entrez le chemin complet vers le dossier StandaloneWindows64
    echo  Exemple : C:\Program Files (x86)\Steam\steamapps\common\ZERO PARADES For Dead Spies\ZeroParades_Data\StreamingAssets\aa\StandaloneWindows64
    echo.
    set /p "GAME_PATH=Chemin : "
)

if not exist "%GAME_PATH%\%BUNDLE_NAME%" (
    echo.
    echo  [ERREUR] Fichier bundle non trouvé dans : %GAME_PATH%
    echo  Vérifiez que Zero Parades est bien installé via Steam.
    echo.
    pause
    exit /b 1
)

echo  Jeu trouvé : %GAME_PATH%
echo.

echo [2/4] Sauvegarde de l'original (Allemand)...
copy /y "%GAME_PATH%\%BUNDLE_NAME%" "%GAME_PATH%\%BUNDLE_NAME%.bak_allemand" >nul
echo  Backup créé : %BUNDLE_NAME%.bak_allemand
echo.

echo [3/4] Installation de la traduction française...
copy /y "%~dp0%BUNDLE_NAME%" "%GAME_PATH%\%BUNDLE_NAME%" >nul
echo  Bundle FR installé avec succès.
echo.

echo [4/4] Vérification...
if exist "%GAME_PATH%\%BUNDLE_NAME%" (
    echo  Fichier présent. Installation OK.
) else (
    echo  [ERREUR] Le fichier n'a pas pu être copié.
    pause
    exit /b 1
)

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   INSTALLATION RÉUSSIE !                    ║
echo  ║                                             ║
echo  ║   Dans le jeu :                            ║
echo  ║   Paramètres → Langue → "Allemand"         ║
echo  ║   Le jeu sera en FRANÇAIS.                  ║
echo  ║                                             ║
echo  ║   Pour désinstaller : relancez ce script   ║
echo  ║   et choisissez l'option restauration.     ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  Merci d'avoir soutenu NetroIA ! ♥
echo  Suivez-nous : netroia.tech
echo.
pause
