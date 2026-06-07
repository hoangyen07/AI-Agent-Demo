# 🤖 Tech Team AI Agent — Demo v1.0

AI Co-Pilot cho Dev và QC, kiến trúc **Global Core + Local Project Knowledge**.

---

## ⚡ Quick Start

### 1. Lấy Gemini API Key
Truy cập https://aistudio.google.com/app/apikey — free tier đủ dùng cho demo.

### 2. Cấu hình
```bash
cp backend/.env.example backend/.env
# Mở backend/.env và điền GEMINI_API_KEY
```

### 3. Chạy
```bash
chmod +x start.sh
bash start.sh
```

Mở trình duyệt: **http://localhost:5173**

---

## 🏗️ Kiến trúc

```
┌─────────────────────────────────────────────┐
│              React Frontend                  │
│   Sidebar (Projects + Role) + Chat UI        │
│   Admin Portal (Upload docs)                 │
└──────────────────┬──────────────────────────┘
                   │ HTTP / SSE Stream
┌──────────────────▼──────────────────────────┐
│            FastAPI Backend                   │
│                                             │
│  POST /api/v1/chat/stream                   │
│  POST /api/v1/projects/upload-doc           │
│  GET  /api/v1/projects/                     │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│  ChromaDB   │         │  Gemini     │
│  (RAG +     │────────▶│  1.5 Flash  │
│  Metadata   │ context │  (LLM)      │
│  Filter)    │         └─────────────┘
└─────────────┘
```

**Luồng xử lý mỗi câu hỏi:**
1. User chọn Project + Role (QC/Dev) → gõ câu hỏi
2. Backend nhận `project_id` → query ChromaDB với metadata filter
3. Chỉ lấy tài liệu đặc tả của đúng project đó (~500-800 tokens)
4. Ghép: System Prompt chuẩn chung + Context đặc tả + Câu hỏi → gửi Gemini
5. Stream response về FE từng token

---

## 📁 Cấu trúc project

```
agent-demo/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings từ .env
│   │   ├── schemas.py           # Pydantic models
│   │   ├── api/
│   │   │   ├── chat_router.py   # POST /chat/stream (SSE)
│   │   │   └── project_router.py# Upload doc, list projects
│   │   ├── services/
│   │   │   └── agent_service.py # Gemini + System Prompt + RAG
│   │   └── database/
│   │       └── vector_db.py     # ChromaDB operations
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── store/
│       │   └── globalContext.jsx  # Global state (project, role)
│       ├── services/
│       │   └── api.js             # Fetch + SSE streaming
│       └── components/
│           ├── Chat/
│           │   ├── ChatWindow.jsx  # Main chat UI
│           │   ├── MessageBubble.jsx # Markdown render + copy
│           │   ├── QuickPrompts.jsx  # Shortcut buttons
│           │   └── Sidebar.jsx       # Project list + role switcher
│           └── Admin/
│               └── AdminPortal.jsx  # Upload tài liệu
│
└── start.sh  # One-command startup
```

---

## 🎯 Cách dùng cho Demo

### Bước 1: Tạo dự án và upload tài liệu
1. Click **"Thêm dự án"** ở sidebar
2. Điền mã dự án (ví dụ: `fintech`) và tên hiển thị
3. Upload file BRD/SRS/API Spec (PDF, DOCX, MD đều được)
4. Chờ xử lý xong → Click **"Bắt đầu chat ngay"**

### Bước 2: Chat với Agent

**Với role QC:**
- Click tab **QC** ở sidebar
- Dùng Quick Prompt **"Viết Test Case"** → điền tên tính năng
- Agent trả ra bảng Jira format với đủ Happy/Negative/Edge case

**Với role Dev:**
- Click tab **Dev** ở sidebar  
- Dùng Quick Prompt **"Tạo MR Template"** → mô tả tính năng
- Agent trả ra MR description đúng chuẩn GitLab

### Bước 3: Demo metadata isolation
- Tạo 2 dự án khác nhau (ví dụ: `fintech` và `ecommerce`)
- Upload tài liệu khác nhau cho mỗi dự án
- Hỏi cùng một câu, chọn project khác nhau → output khác nhau

---

## 🔧 Cấu hình nâng cao

### Thay đổi LLM model
Trong `backend/app/services/agent_service.py`:
```python
model_name="gemini-2.5-flash"  # Hoặc "gemini-2.5-pro" cho chất lượng cao hơn
```

### Tuning RAG
Trong `backend/app/database/vector_db.py`:
```python
chunk_size=800    # Tăng nếu tài liệu cần nhiều context hơn
chunk_overlap=150 # Tăng nếu bị mất thông tin ở ranh giới chunk
k=5               # Số chunks retrieve mỗi query
```

### Thêm loại file hỗ trợ
Trong `backend/app/api/project_router.py`:
```python
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "md", "txt"}  # Thêm vào đây
```

---

## ❓ FAQ

**Q: Agent trả lời sai hoặc không biết?**
A: Kiểm tra tài liệu đã upload chưa (xem số chunks trong sidebar). Nếu có, thử hỏi lại với từ khóa cụ thể hơn có trong tài liệu.

**Q: Tài liệu công ty có bị gửi ra ngoài không?**
A: Tài liệu được lưu local trong ChromaDB trên máy của bạn. Chỉ có các đoạn liên quan (~500 tokens) được gửi kèm mỗi câu hỏi đến Gemini API. Không có dữ liệu nào được dùng để training model.

**Q: Muốn reset toàn bộ data?**
A: Xóa thư mục `backend/chroma_db/` và restart backend.

**Q: Chạy production thì cần làm gì thêm?**
A: Phase 1 là demo — cần thêm authentication, persistent project registry (database), và deploy lên server. Để discuss cho Phase 2.

---

## 📋 Tech Stack

| Layer | Tech |
|-------|------|
| LLM | Google Gemini 1.5 Flash |
| Vector DB | ChromaDB (local) |
| Embeddings | Google text-embedding-001 |
| Backend | FastAPI + Python 3.11+ |
| Frontend | React 18 + Tailwind CSS v3 |
| Streaming | Server-Sent Events (SSE) |
| Doc parsing | PyPDF + python-docx |
