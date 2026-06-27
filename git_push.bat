@echo off
chcp 65001 >nul
cd /d F:\CUOTI_Lingma
git add -A
git commit -m "fix: 第二轮QA修复 - 安全加固、异步优化、CSP收紧、文档端口统一、.gitignore完善"
git push
echo DONE
