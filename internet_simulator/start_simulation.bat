@echo off
echo Starting Internet Simulator...
echo.
echo Opening 3 terminals for router, user, and ali clients
echo.
echo Terminal 1: Router
start "Router" cmd /k "python main.py --config configs/router.json"
timeout /t 2 /nobreak > nul

echo Terminal 2: User Client  
start "User" cmd /k "python main.py --config configs/user.json"
timeout /t 2 /nobreak > nul

echo Terminal 3: Ali Client
start "Ali" cmd /k "python main.py --config configs/ali.json"

echo.
echo All terminals started! You can now send messages between nodes.
echo.
echo Usage examples:
echo   From User: send_message 192.168.1.2 "Hello Ali!" udp
echo   From Ali:  send_message 192.168.1.6 "Hello User!" udp
echo.
pause
