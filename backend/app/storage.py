import json
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile

from .models import ProjectState, now_iso
from .settings import PROJECTS_DIR, ensure_runtime_dirs


def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id


def state_path(project_id: str) -> Path:
    return project_dir(project_id) / "project.json"


def media_url(path: Path) -> str:
    relative = path.resolve().relative_to(PROJECTS_DIR.resolve())
    return "/media/projects/" + "/".join(relative.parts)


def read_project(project_id: str) -> ProjectState:
    path = state_path(project_id)
    if not path.exists():
        raise FileNotFoundError(project_id)
    return ProjectState(**json.loads(path.read_text(encoding="utf-8")))


def write_project(project: ProjectState) -> ProjectState:
    data = project.dict()
    data["updated_at"] = now_iso()
    project = ProjectState(**data)
    target = state_path(project.id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(project.dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return project


def list_projects() -> List[ProjectState]:
    ensure_runtime_dirs()
    projects: List[ProjectState] = []
    for item in sorted(PROJECTS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if item.is_dir() and (item / "project.json").exists():
            projects.append(read_project(item.name))
    return projects


def create_project(name: str, source_filename: str, source_path: Path) -> ProjectState:
    ensure_runtime_dirs()
    project_id = uuid.uuid4().hex[:12]
    root = project_dir(project_id)
    root.mkdir(parents=True, exist_ok=True)
    project = ProjectState(
        id=project_id,
        name=name,
        source_path=str(source_path),
        source_filename=source_filename,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    return write_project(project)


def import_from_path(path: Path, name: str | None = None) -> ProjectState:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))
    project_id = uuid.uuid4().hex[:12]
    root = project_dir(project_id)
    root.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix or ".mp4"
    target = root / f"source{suffix}"
    shutil.copy2(path, target)
    project = ProjectState(
        id=project_id,
        name=name or path.stem,
        source_path=str(target),
        source_filename=path.name,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    return write_project(project)


async def import_upload(file: UploadFile) -> ProjectState:
    filename = file.filename or "video.mp4"
    project_id = uuid.uuid4().hex[:12]
    root = project_dir(project_id)
    root.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix or ".mp4"
    target = root / f"source{suffix}"
    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)
    project = ProjectState(
        id=project_id,
        name=Path(filename).stem,
        source_path=str(target),
        source_filename=filename,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    return write_project(project)

