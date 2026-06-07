from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat_router import router as chat_router
from app.api.project_router import router as project_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Tech Team AI Agent",
    description="AI Co-Pilot cho Dev và QC — Global Core + Local Project Knowledge",
    version="1.0.0-demo"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(project_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0-demo"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
