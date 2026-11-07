@echo off
title PS Details - Khammam (https://dpokmm.panchayatautomation.in/ps-data)
cd /d "%~dp0"
cls

echo ===========================================================================
echo   DISTRICT PANCHAYAT OFFICE, KHAMMAM
echo   Details of Panchayat Secretaries Working in Khammam District
echo   Public Domain: https://dpokmm.panchayatautomation.in/ps-data
echo ===========================================================================
echo.

python run_cloudflare_portal.py
pause
