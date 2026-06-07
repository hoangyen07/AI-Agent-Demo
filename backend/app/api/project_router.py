from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.database.vector_db import ingest_file, get_project_documents, get_all_projects
from app.schemas import UploadResponse, ProjectInfo

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "md", "txt"}

# In-memory project registry (extend with DB for production)
PROJECT_REGISTRY: dict[str, str] = {}


@router.post("/upload-doc", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    project_name: str = Form(...),
):
    """Upload a document and ingest it into the vector store for a project."""
    ext = file.filename.lower().split(".")[-1] if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' không được hỗ trợ. Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="File quá lớn (tối đa 20MB)")

    PROJECT_REGISTRY[project_id] = project_name

    chunks_added = ingest_file(
        file_bytes=contents,
        filename=file.filename,
        project_id=project_id
    )

    return UploadResponse(
        status="success",
        message=f"Đã nạp thành công '{file.filename}' vào dự án '{project_name}'",
        chunks_added=chunks_added,
        project_id=project_id
    )


@router.get("/", response_model=list[ProjectInfo])
async def list_projects():
    """Return all projects with their ingested documents."""
    project_ids = get_all_projects()

    # Merge with registry names
    result = []
    for pid in project_ids:
        docs = get_project_documents(pid)
        result.append(ProjectInfo(
            project_id=pid,
            project_name=PROJECT_REGISTRY.get(pid, pid),
            documents=docs,
            total_chunks=sum(d["chunks"] for d in docs)
        ))

    # Also include projects from registry that may not have docs yet
    for pid, pname in PROJECT_REGISTRY.items():
        if pid not in project_ids:
            result.append(ProjectInfo(
                project_id=pid,
                project_name=pname,
                documents=[],
                total_chunks=0
            ))

    return result


@router.get("/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str):
    """Get details of a specific project."""
    docs = get_project_documents(project_id)
    return ProjectInfo(
        project_id=project_id,
        project_name=PROJECT_REGISTRY.get(project_id, project_id),
        documents=docs,
        total_chunks=sum(d["chunks"] for d in docs)
    )
