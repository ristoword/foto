@echo off
title AppFoto Dashboard
cd /d "%~dp0"
.venv\Scripts\streamlit run dashboard.py
