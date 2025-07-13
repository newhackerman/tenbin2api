@echo off
echo 启动FamilyAI 伴侣聊天界面服务器...
echo.
echo API服务器: http://127.0.0.1:8401
echo 聊天界面: http://127.0.0.1:8402/chat.html
echo.
python -m http.server 8402
pause