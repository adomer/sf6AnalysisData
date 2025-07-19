@echo off
REM Batch file to run SF6 data export
REM Schedule this with Windows Task Scheduler

echo Starting SF6 Data Export - %date% %time%

REM Change to the project directory (modify this path for your setup)
cd /d "%~dp0"

REM Create output directory if it doesn't exist
if not exist "output" mkdir output

REM Run all spiders
echo Running fighting_stats spider...
python -c "from spiders.fighting_stats_spider import FightingStatsSpider; spider = FightingStatsSpider(); spider.setup_selenium(None)" 2>&1
echo Fighting stats spider exit code: %ERRORLEVEL%

if %ERRORLEVEL% NEQ 0 (
    echo Error running fighting_stats spider with exit code %ERRORLEVEL%
    goto :error
)

echo Running street_fighter_spider...
python main.py 2>&1
echo Street fighter spider exit code: %ERRORLEVEL%

if %ERRORLEVEL% NEQ 0 (
    echo Error running street_fighter_spider with exit code %ERRORLEVEL%
    goto :error
)


echo Export completed successfully - %date% %time%

REM Optional: Copy files to a backup location
REM Set SF6_BACKUP_DIR environment variable to enable backups
if defined SF6_BACKUP_DIR (
    if not exist "%SF6_BACKUP_DIR%" mkdir "%SF6_BACKUP_DIR%"
    xcopy "output\*.csv" "%SF6_BACKUP_DIR%\%date:~-4,4%-%date:~-10,2%-%date:~-7,2%\" /Y /I
    echo Files backed up to %SF6_BACKUP_DIR%
)

goto :end

:error
echo Export failed with error code %ERRORLEVEL%
exit /b %ERRORLEVEL%

:end
REM Remove pause for automated runs
REM pause