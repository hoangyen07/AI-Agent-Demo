import os
from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
import chromadb
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction

settings = get_settings()

# 1. Khởi tạo lại cấu hình giống hệt trong source code của bạn
ef = GoogleGenerativeAiEmbeddingFunction(
    api_key=settings.gemini_api_key,
    model_name="models/embedding-001"
)
client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

print(f"--- ĐANG KẾT NỐI VÀO DATABASE: {settings.chroma_persist_dir} ---")
try:
    # 2. Lấy collection ra kèm theo hàm Embedding để tránh lỗi
    collection = client.get_collection(name="agent_knowledge", embedding_function=ef)
    total_records = collection.count()
    print(f"✅ Tìm thấy Collection 'agent_knowledge' thành công!")
    print(f"📊 Tổng số đoạn văn bản (chunks) đang lưu trữ: {total_records}\n")
    
    if total_records > 0:
        # Lấy thử 5 đoạn dữ liệu đầu tiên để kiểm tra
        results = collection.get(limit=5, include=["documents", "metadatas"])
        print("--- HIỂN THỊ 5 ĐOẠN DỮ LIỆU ĐẦU TIÊN ---")
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
            print(f"[{i+1}] Dự án: {meta.get('project_id')} | File gốc: {meta.get('source_file')}")
            print(f"Nội dung: {doc[:150]}...") # In 150 ký tự đầu
            print("-" * 40)
    else:
        print("📭 Cơ sở dữ liệu đang trống. Hãy chạy API Upload file trước.")

except Exception as e:
    print(f"❌ Lỗi khi đọc dữ liệu: {e}")