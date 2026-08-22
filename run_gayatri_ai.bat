@echo off
setlocal enabledelayedexpansion
title Gayatri AI - Installer / Launcher (DBERT Incubation - Internship Batch Aug 2026)

:: ================================================================
:: Gayatri AI - Installer / Auto-Updating Launcher
:: DBERT Incubation Program - Internship Batch: August 2026
:: Beta Release
::
:: Re-run this file any time - it checks what's already installed
:: or configured and only acts on what's missing, then updates the
:: app code and launches it.
:: ================================================================

set "INSTALL_ROOT=%USERPROFILE%\GayatriAI"
set "REPO_DIR=%INSTALL_ROOT%\Gayatri-AI"
set "REPO_URL=https://github.com/Gayatri-Education/Gayatri-AI.git"
set "LM_MODEL=qwen2.5-3b-instruct@q4_k_m"
set "LOG_DIR=%INSTALL_ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\install_log.txt"
set "CONSENT_FILE=%INSTALL_ROOT%\consent_accepted.txt"
set "LMSTUDIO_EXE=%LOCALAPPDATA%\Programs\LM Studio\LM Studio.exe"
set "MIN_RAM_GB=8"
set "MIN_DISK_GB=10"

if not exist "%INSTALL_ROOT%" mkdir "%INSTALL_ROOT%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] ===== Run started ===== >> "%LOG_FILE%"

:: ================================================================
:: PHASE 0 - CONSENT SCREEN
:: ================================================================
if not exist "%CONSENT_FILE%" (
    cls
    echo ================================================================
    echo   GAYATRI AI  -  BETA SOFTWARE NOTICE AND USER CONSENT
    echo   DBERT Incubation Program
    echo ================================================================
    echo.
    echo This software ("Gayatri AI"^) is developed under the DBERT
    echo Incubation Program and is provided as a BETA release for
    echo evaluation and internal use by the Internship Batch of
    echo August 2026.
    echo.
    echo By proceeding, you acknowledge and agree to the following:
    echo.
    echo   1. BETA STATUS
    echo      This is pre-release software under active development.
    echo      It may contain bugs, incomplete features, or unexpected
    echo      behavior, and is provided "as is" without warranty of
    echo      any kind, express or implied.
    echo.
    echo   2. DATA COLLECTION
    echo      Data you provide to, generate through, or that is
    echo      otherwise captured by this application - including but
    echo      not limited to inputs, outputs, conversation history,
    echo      and usage/diagnostic logs - will be collected and
    echo      retained for evaluation, improvement, and internal
    echo      program purposes.
    echo.
    echo   3. OWNERSHIP
    echo      All such data, and any derivative work products
    echo      generated from it, are and shall remain the property
    echo      of DBERT.
    echo.
    echo   4. SCOPE
    echo      This release is authorized for use solely by
    echo      participants of the DBERT Internship Batch of August
    echo      2026, for the purposes of that program.
    echo.
    echo   5. LOCAL COMPONENTS
    echo      This installer will download and configure third-party
    echo      software (including Python, Git, and LM Studio^) and an
    echo      AI language model on this device to run the application
    echo      locally. Standard terms of those respective providers
    echo      apply to those components.
    echo.
    echo This is a summary notice. It does not replace any separate
    echo program agreement, NDA, or policy provided to you by DBERT.
    echo If you have not received or do not understand those terms,
    echo stop here and contact your program coordinator before
    echo continuing.
    echo.
    echo ----------------------------------------------------------------
    echo To continue, type your full name, then type YES to confirm
    echo you have read, understood, and agree to the above.
    echo ----------------------------------------------------------------
    echo.
    set "USER_NAME="
    set "USER_CONFIRM="
    set /p USER_NAME="Your full name: "
    if "!USER_NAME!"=="" (
        echo.
        echo A name is required to proceed. Exiting.
        echo [%date% %time%] CONSENT DECLINED - no name entered >> "%LOG_FILE%"
        pause
        exit /b 1
    )
    set /p USER_CONFIRM="Type YES to agree and continue: "
    if /i not "!USER_CONFIRM!"=="YES" (
        echo.
        echo Consent not confirmed. Setup cannot continue. Exiting.
        echo [%date% %time%] CONSENT DECLINED - user: !USER_NAME! >> "%LOG_FILE%"
        pause
        exit /b 1
    )
    (
        echo Gayatri AI - Beta Consent Record
        echo DBERT Incubation Program - Internship Batch: August 2026
        echo Name: !USER_NAME!
        echo Confirmation: YES
        echo Timestamp: %date% %time%
        echo Machine: %COMPUTERNAME%
    ) > "%CONSENT_FILE%"
    echo [%date% %time%] CONSENT ACCEPTED - user: !USER_NAME! >> "%LOG_FILE%"
    echo.
    echo Thank you, !USER_NAME!. Proceeding with setup...
    timeout /t 2 >nul
) else (
    echo Consent already on file for this device - skipping notice.
    echo [%date% %time%] Consent already recorded - skipping >> "%LOG_FILE%"
)

echo.
echo ================================================================
echo   Gayatri AI - Setup and Launch
echo ================================================================
echo.
echo Checking your system and installing only what's missing.
echo First-time setup can take 15-30+ minutes depending on what's
echo already present and your connection speed. Later runs are
echo much faster.
echo.

:: ================================================================
:: PHASE 0.5 - HARDWARE CHECK (before touching LM Studio)
:: ================================================================
echo [Hardware Check] Verifying this machine meets minimum requirements...

set "HW_FAIL=0"
set "HW_REASON="

powershell -NoProfile -Command ^
  "$ErrorActionPreference='SilentlyContinue'; $r = Add-Type -MemberDefinition '[DllImport(\"kernel32.dll\")] public static extern bool IsProcessorFeaturePresent(int f);' -Name Cpu -PassThru -ErrorAction SilentlyContinue; if ($r) { if ($r::IsProcessorFeaturePresent(40)) { exit 0 } else { exit 1 } } else { exit 2 }" >nul 2>&1
set "AVX2_RESULT=%errorlevel%"
if "%AVX2_RESULT%"=="1" (
    set "HW_FAIL=1"
    set "HW_REASON=!HW_REASON! - CPU does not support AVX2, which LM Studio requires."
)

for /f "usebackq tokens=*" %%R in (`powershell -NoProfile -Command "[math]::Floor((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)"`) do set "TOTAL_RAM_GB=%%R"
if "%TOTAL_RAM_GB%"=="" set "TOTAL_RAM_GB=0"
if %TOTAL_RAM_GB% LSS %MIN_RAM_GB% (
    set "HW_FAIL=1"
    set "HW_REASON=!HW_REASON! - Only %TOTAL_RAM_GB%GB RAM detected, minimum %MIN_RAM_GB%GB required."
)

for /f "usebackq tokens=*" %%D in (`powershell -NoProfile -Command "[math]::Floor((Get-PSDrive -Name ('%~d0'.TrimEnd(':')) ).Free / 1GB)"`) do set "FREE_DISK_GB=%%D"
if "%FREE_DISK_GB%"=="" set "FREE_DISK_GB=0"
if %FREE_DISK_GB% LSS %MIN_DISK_GB% (
    set "HW_FAIL=1"
    set "HW_REASON=!HW_REASON! - Only %FREE_DISK_GB%GB free disk space, minimum %MIN_DISK_GB%GB required."
)

if "%HW_FAIL%"=="1" (
    echo.
    echo ================================================================
    echo   SETUP CANNOT CONTINUE - HARDWARE REQUIREMENTS NOT MET
    echo ================================================================
    echo !HW_REASON!
    echo.
    echo Gayatri AI runs an AI model locally on this machine via LM
    echo Studio, which needs the above minimums. This is a hardware
    echo limitation and cannot be resolved by re-running this script.
    echo Please try on a different machine, or contact your program
    echo coordinator.
    echo [%date% %time%] FAILED - hardware check: !HW_REASON! >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo   CPU (AVX2): OK
echo   RAM: %TOTAL_RAM_GB%GB detected (minimum %MIN_RAM_GB%GB^) - OK
echo   Free disk space: %FREE_DISK_GB%GB detected (minimum %MIN_DISK_GB%GB^) - OK
echo [%date% %time%] Hardware check passed - RAM=%TOTAL_RAM_GB%GB Disk=%FREE_DISK_GB%GB >> "%LOG_FILE%"

:: ================================================================
:: PHASE 1 - System dependencies (Git, Python, LM Studio)
:: ================================================================
echo.
echo [1/6] Checking Git...
where git >nul 2>&1
if errorlevel 1 (
    echo   Not found - installing Git...
    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    call :RefreshPath
) else (
    for /f "tokens=*" %%V in ('git --version') do echo   Found: %%V
)

echo [1/6] Checking Python...
set "PY_OK=0"
where python >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do set "PY_VER=%%V"
    python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY_OK=1"
        echo   Found: !PY_VER! - meets minimum (3.10+^)
    ) else (
        echo   Found: !PY_VER! - below minimum (3.10+^), installing a supported version alongside it
    )
)
if "%PY_OK%"=="0" (
    echo   Installing Python 3.12...
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    call :RefreshPath
)

echo [1/6] Checking LM Studio...
if not exist "%LMSTUDIO_EXE%" (
    echo   Not found - installing LM Studio...
    winget install --id ElementLabs.LMStudio -e --silent --accept-package-agreements --accept-source-agreements
) else (
    echo   Found - already installed, skipping.
)
echo [%date% %time%] Phase 1 complete - system deps checked/installed >> "%LOG_FILE%"

:: ================================================================
:: PHASE 2 - Get / update the code
:: ================================================================
echo.
echo [2/6] Fetching latest code...
if exist "%REPO_DIR%\.git" (
    pushd "%REPO_DIR%"
    if exist "gayatri.db" copy /Y "gayatri.db" "gayatri.db.local-backup" >nul
    git pull
    if exist "gayatri.db.local-backup" (
        copy /Y "gayatri.db.local-backup" "gayatri.db" >nul
        del "gayatri.db.local-backup" >nul
    )
    popd
) else (
    git clone "%REPO_URL%" "%REPO_DIR%"
)
if not exist "%REPO_DIR%\main.py" (
    echo [ERROR] main.py not found after clone/pull - check your
    echo internet connection and that the repository URL is correct.
    echo [%date% %time%] FAILED - repo fetch >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo [%date% %time%] Phase 2 complete - repo up to date >> "%LOG_FILE%"

:: ================================================================
:: PHASE 3 - Python environment
:: ================================================================
echo.
echo [3/6] Setting up Python environment...
pushd "%REPO_DIR%"
if not exist "venv" (
    python -m venv venv
) else (
    echo   Existing virtual environment found - reusing it.
)
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Installing Python packages failed - see the
    echo messages above for which package caused it.
    echo [%date% %time%] FAILED - pip install >> "%LOG_FILE%"
    popd
    pause
    exit /b 1
)
echo [%date% %time%] Phase 3 complete - dependencies installed >> "%LOG_FILE%"

:: ================================================================
:: PHASE 4 - Pre-warm the embedding model
:: ================================================================
echo.
echo [4/6] Preparing embedding model...
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
echo [%date% %time%] Phase 4 complete - embedding model cached >> "%LOG_FILE%"

:: ================================================================
:: PHASE 5 - LM Studio: bootstrap CLI, respect existing setup
:: ================================================================
echo.
echo [5/6] Preparing local AI model...
where lms >nul 2>&1
if errorlevel 1 (
    echo   First-time LM Studio setup - its window will open briefly...
    start "" "%LMSTUDIO_EXE%"
    call :WaitForLms
    if errorlevel 1 (
        echo [WARNING] Could not detect the 'lms' command yet.
        echo Make sure the LM Studio window fully opened, then
        echo re-run this script to continue - this step is safe
        echo to retry.
        echo [%date% %time%] WARNING - lms not detected after first launch >> "%LOG_FILE%"
        popd
        pause
        exit /b 1
    )
)

lms server start >nul 2>&1

set "EXISTING_MODEL="
for /f "usebackq tokens=*" %%M in (`lms ps 2^>nul ^| findstr /r /c:"."`) do (
    if not defined EXISTING_MODEL set "EXISTING_MODEL=%%M"
)
if defined EXISTING_MODEL (
    echo   A model is already loaded in LM Studio - using it as-is:
    echo     !EXISTING_MODEL!
    echo   Skipping default model download.
) else (
    set "HAS_ANY_MODEL="
    for /f "usebackq tokens=*" %%L in (`lms ls 2^>nul ^| findstr /r /c:"."`) do (
        if not defined HAS_ANY_MODEL set "HAS_ANY_MODEL=%%L"
    )
    if defined HAS_ANY_MODEL (
        echo   Existing downloaded model(s^) found but none loaded.
        echo   Loading the most recently used model...
        lms load --exact --yes >nul 2>&1
        if errorlevel 1 (
            echo   Could not auto-load an existing model - loading
            echo   the default instead.
            lms get %LM_MODEL% -y
            lms load %LM_MODEL%
        )
    ) else (
        echo   No models found - downloading the default (~2GB^)...
        lms get %LM_MODEL% -y
        lms load %LM_MODEL%
    )
)
echo [%date% %time%] Phase 5 complete - local model ready >> "%LOG_FILE%"

:: ================================================================
:: PHASE 6 - Launch
:: ================================================================
echo.
echo [6/6] Launching Gayatri AI...
echo.
python main.py
set "APP_EXIT=%errorlevel%"
popd
if not "%APP_EXIT%"=="0" (
    echo.
    echo [ERROR] Gayatri AI closed with an error - check the
    echo messages above for details.
    echo [%date% %time%] App exited with code %APP_EXIT% >> "%LOG_FILE%"
    pause
)

:: ================================================================
:: Optional Desktop shortcut (offered once)
:: ================================================================
if not exist "%INSTALL_ROOT%\.shortcut_done" (
    echo.
    set /p MAKE_SHORTCUT="Create a Desktop shortcut for next time? (Y/N): "
    if /i "!MAKE_SHORTCUT!"=="Y" call :CreateShortcut
    echo done > "%INSTALL_ROOT%\.shortcut_done"
)

exit /b 0

:: ===================== Subroutines =====================

:RefreshPath
for /f "usebackq tokens=*" %%P in (`powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%P"
exit /b 0

:WaitForLms
for /L %%i in (1,1,20) do (
    call :RefreshPath
    where lms >nul 2>&1
    if not errorlevel 1 exit /b 0
    timeout /t 3 >nul
)
exit /b 1

:CreateShortcut
set "VBS=%TEMP%\gayatri_shortcut.vbs"
> "%VBS%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Gayatri AI.lnk"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%~f0"
>> "%VBS%" echo oLink.WorkingDirectory = "%~dp0"
>> "%VBS%" echo oLink.Description = "Gayatri AI"
>> "%VBS%" echo oLink.Save
cscript //nologo "%VBS%"
del "%VBS%"
exit /b 0
