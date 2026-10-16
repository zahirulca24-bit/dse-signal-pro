@echo off
title DSE Signal Pro - Automated Smoke Test Suite
color 0B
cd /d "%~dp0"

echo =====================================================================
echo           RUNNING DSE SIGNAL PRO AUTOMATED SMOKE TESTS
echo =====================================================================
echo.

Backend\.venv\Scripts\python.exe tests\smoke_test.py

pause
