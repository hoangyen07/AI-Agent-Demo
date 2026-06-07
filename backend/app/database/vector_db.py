import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_core.documents import Document
from google import genai
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

import tempfile, os
from app.config import get_settings

settings = get_settings()
COLLECTION_NAME = "agent_knowledge"

class ModernGoogleEmbeddingFunction(EmbeddingFunction):
    """
    Custom Embedding Function tương thích 100% với SDK google-genai mới,
    thay thế hoàn toàn cho GoogleGenerativeAiEmbeddingFunction cũ bị lỗi.
    """
    def __init__(self, api_key: str, model_name: str = "text-embedding-004"):
        # Sử dụng client mới từ thư viện google-genai
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        # Gọi API lấy embedding theo chuẩn của thư viện mới
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=input,
        )
        
        # Trích xuất danh sách các vector số (embeddings) trả về cho ChromaDB
        # Định dạng: [ [0.1, 0.2, ...], [0.3, 0.4, ...] ]
        return [emb.values for emb in response.embeddings]

def _get_ef():
    # Sử dụng Class mới + model chuẩn hiện tại là "gemini-embedding-001"
    return ModernGoogleEmbeddingFunction(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_embedding_model # Model embedding mới nhất, thay thế "models/embedding-001" cũ
    )

def _get_client():
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)

def _get_collection():
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_ef()
    )


def ingest_file(file_bytes: bytes, filename: str, project_id: str) -> int:
    ext = filename.lower().split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == "pdf":
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
        elif ext in ("docx", "doc"):
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
        else:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            docs = [Document(page_content=text)]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=150,
            separators=["\n\n", "\n", ".", " "]
        )
        chunks = splitter.split_documents(docs)

        if not chunks:
            return 0

        collection = _get_collection()

        # Build data for chromadb
        ids, documents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{project_id}_{filename}_{i}")
            documents.append(chunk.page_content)
            metadatas.append({
                "project_id": project_id,
                "source_file": filename,
            })

        # Upsert in batches of 50
        batch = 50
        for start in range(0, len(ids), batch):
            collection.upsert(
                ids=ids[start:start+batch],
                documents=documents[start:start+batch],
                metadatas=metadatas[start:start+batch],
            )

        return len(chunks)
    finally:
        os.unlink(tmp_path)


def retrieve_context(query: str, project_id: str, k: int = 5) -> str:
    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=min(k, collection.count()),
            where={"project_id": project_id},
            include=["documents", "metadatas"]
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            return ""

        parts = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source_file", "unknown")
            parts.append(f"[Nguồn: {source}]\n{doc}")

        return "\n\n---\n\n".join(parts)
    except Exception as e:
        print(f"[RAG] retrieve error: {e}")
        return ""


def get_project_documents(project_id: str) -> list[dict]:
    try:
        collection = _get_collection()
        results = collection.get(
            where={"project_id": project_id},
            include=["metadatas"]
        )
        file_chunks: dict[str, int] = {}
        for meta in results["metadatas"]:
            fname = meta.get("source_file", "unknown")
            file_chunks[fname] = file_chunks.get(fname, 0) + 1
        return [{"filename": f, "source": f, "chunks": c} for f, c in file_chunks.items()]
    except Exception:
        return []


def get_all_projects() -> list[str]:
    try:
        collection = _get_collection()
        results = collection.get(include=["metadatas"])
        ids = {m.get("project_id") for m in results["metadatas"] if m.get("project_id")}
        return sorted(ids)
    except Exception:
        return []
