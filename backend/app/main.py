from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .jobs import job_manager
from .models import AnalyzeRequest, ImportPathRequest, RenderRequest, SegmentListRequest
from .ocr import get_ocr_capabilities
from .settings import PROJECTS_DIR, ensure_runtime_dirs
from .storage import import_from_path, import_upload, list_projects, read_project, write_project
from .video import extract_preview_frames, probe_video, render_video_job

ensure_runtime_dirs()

app = FastAPI(title="Video Text Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8790", "http://localhost:8790"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media/projects", StaticFiles(directory=str(PROJECTS_DIR)), name="projects-media")


@app.get("/api/health")
def health() -> dict:
    capabilities = get_ocr_capabilities()
    return {
        "ok": True,
        "ocr": {"available": capabilities.available, "engine": capabilities.engine},
    }


@app.get("/api/projects")
def get_projects() -> list[dict]:
    return [project.dict() for project in list_projects()]


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict:
    try:
        return read_project(project_id).dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@app.post("/api/projects/import-path")
def create_project_from_path(payload: ImportPathRequest) -> dict:
    try:
        project = import_from_path(Path(payload.path), payload.name)
        project.metadata = probe_video(Path(project.source_path))
        return write_project(project).dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects/upload")
async def upload_video(file: UploadFile = File(...)) -> dict:
    try:
        project = await import_upload(file)
        project.metadata = probe_video(Path(project.source_path))
        return write_project(project).dict()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/analyze")
def analyze_project(project_id: str, payload: AnalyzeRequest) -> dict:
    try:
        project = read_project(project_id)
        project = extract_preview_frames(project, payload.sample_count)
        return project.dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/projects/{project_id}/segments")
def save_segments(project_id: str, payload: SegmentListRequest) -> dict:
    try:
        project = read_project(project_id)
        project.segments = payload.segments
        return write_project(project).dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@app.post("/api/projects/{project_id}/render")
def render_project(project_id: str, payload: RenderRequest) -> dict:
    try:
        project = read_project(project_id)
        segments = payload.segments if payload.segments is not None else project.segments
        if not segments:
            raise HTTPException(status_code=400, detail="No text regions to render")
        project.segments = segments
        project = write_project(project)
        job = job_manager.submit("render", render_video_job, project, segments, payload.output_name)
        return job.dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        return job_manager.get(job_id).dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

