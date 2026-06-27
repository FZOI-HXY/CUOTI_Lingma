@echo off
cd /d F:\CUOTI_Lingma
git add -A
git commit -m "fix: conditionally set pool params for SQLite in database.py - avoid passing pool_size=None to create_engine"
git push
pause
