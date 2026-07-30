@echo off
title AppFoto
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0launcher.ps1"
