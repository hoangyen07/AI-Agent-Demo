#!/bin/bash

# Tech Team AI Agent — Demo Startup Script
# Chạy: bash start.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ████████╗███████╗ ██████╗██╗  ██╗"
echo "     ██╔══╝██╔════╝██╔════╝██║  ██║"
echo "     ██║   █████╗  ██║     ███████║"
echo "     ██║   ██╔══╝  ██║     ██╔══██║"
echo "     ██║   ███████╗╚██████╗██║  ██║"
echo "     ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}  Tech Team AI Agent — Demo v1.0${NC}"
echo ""

# Check .env
if [ ! -f "backend/.env" ]; then
  echo -e "${YELLOW}⚠️  Chưa có file backend/.env${NC}"
  echo -e "   Tạo file từ mẫu và điền GEMINI_API_KEY:"
  echo -e "   ${BLUE}cp backend/.env.example backend/.env${NC}"
  echo ""
  read -p "Nhấn Enter sau khi đã tạo .env để tiếp tục..."
fi

# Check Gemini API Key
source backend/.env 2>/dev/null
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
  echo -e "${RED}❌ GEMINI_API_KEY chưa được cấu hình trong backend/.env${NC}"
  echo -e "   Lấy API key tại: https://aistudio.google.com/app/apikey"
  exit 1
fi

echo -e "${GREEN}✅ Gemini API Key OK${NC}"
echo ""

# Setup Backend
echo -e "${BLUE}[1/4] Cài đặt Backend dependencies...${NC}"
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip3 install -r requirements.txt -q

echo -e "${GREEN}✅ Backend ready${NC}"

# Start Backend
echo -e "${BLUE}[2/4] Khởi động Backend (port 8000)...${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend PID: $BACKEND_PID${NC}"
cd ..

sleep 2

# Setup Frontend
echo -e "${BLUE}[3/4] Cài đặt Frontend dependencies...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
  npm install -q
fi

# Copy env if not exists
if [ ! -f ".env" ]; then
  cp .env.example .env
fi

echo -e "${GREEN}✅ Frontend ready${NC}"

# Start Frontend
echo -e "${BLUE}[4/4] Khởi động Frontend (port 5173)...${NC}"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🚀 Agent đang chạy!${NC}"
echo ""
echo -e "  Frontend:  ${BLUE}http://localhost:5173${NC}"
echo -e "  Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Nhấn ${RED}Ctrl+C${NC} để dừng tất cả"
echo ""

# Cleanup on exit
trap "echo ''; echo 'Đang dừng...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
