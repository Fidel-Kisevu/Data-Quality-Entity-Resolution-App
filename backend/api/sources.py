from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from core.database import get_db
from core.config import get_settings
from models.models import Source, AuditEvent
from services.ingestion import ingest_source

router = APIRouter()
settings = get_settings()

# Repo root: backend/../data/raw
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


@router.get("")
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "source_system": s.source_system,
            "original_filename": s.original_filename,
            "status": s.status,
            "row_count": s.row_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sources
    ]


@router.post("/upload")
async def upload_source(
    file: UploadFile = File(...),
    source_system: str = "CRM",
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel file. Saves to disk and registers the Source."""
    if source_system not in ["CRM", "ERP", "MKT"]:
        raise HTTPException(status_code=400, detail="source_system must be CRM, ERP or MKT")

    filename = file.filename or "upload.csv"
    source_id = str(uuid.uuid4())

    # Persist file to disk: data/raw/{source_id}/{filename}
    target_dir = RAW_DIR / source_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename

    content = await file.read()
    target_path.write_bytes(content)

    source = Source(
        id=source_id,
        name=filename,
        source_system=source_system,
        original_filename=filename,
        status="raw",
        row_count=None,
        stored_path=str(target_path),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(source)
    db.add(AuditEvent(
        event_type="source.uploaded",
        entity_type="source",
        entity_id=source.id,
        actor="system",
        action="upload",
        before_state=None,
        after_state={"filename": filename, "source_system": source_system, "bytes": len(content)},
        notes=f"Uploaded {filename} as {source_system}",
    ))
    db.commit()
    db.refresh(source)

    return {
        "id": source.id,
        "name": source.name,
        "source_system": source.source_system,
        "status": source.status,
        "stored_path": source.stored_path,
        "bytes_received": len(content),
        "next": f"POST /sources/{source.id}/ingest to parse and profile",
    }


@router.post("/{source_id}/ingest")
def ingest(source_id: str, db: Session = Depends(get_db)):
    """Parse the stored file, insert rows, profile, mark as profiled."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if not source.stored_path:
        raise HTTPException(status_code=400, detail="Source has no stored file")

    try:
        result = ingest_source(db, source)
    except FileNotFoundError as e:
        raise HTTPException(status_code=410, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return result


@router.get("/{source_id}")
def get_source(source_id: str, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "id": source.id,
        "name": source.name,
        "source_system": source.source_system,
        "original_filename": source.original_filename,
        "status": source.status,
        "row_count": source.row_count,
        "stored_path": source.stored_path,
        "profile": source.profile_json,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }