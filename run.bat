@echo off
echo Starting claude-lark...
pip install -r requirements.txt
copy /y .env.example .env
echo Please edit .env with your credentials, then press any key to start...
pause
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
