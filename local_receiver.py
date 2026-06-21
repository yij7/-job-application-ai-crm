from datetime import datetime
from pathlib import Path
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


DATA_DIR = Path("data")
SESSION_DIR = DATA_DIR / "extension_sessions"


class CapturedPage(BaseModel):
    page_title: str = ""
    page_url: str = ""
    raw_text: str = ""
    captured_at: str = ""
    page_type: str = ""
    source: str = ""


class ImportSessionRequest(BaseModel):
    session_id: str = ""
    created_at: str = ""
    source: str = "boss_chrome_extension"
    pages: list[CapturedPage] = Field(default_factory=list)


app = FastAPI(title="BossPilot Local Receiver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/import-session")
def import_session(payload: ImportSessionRequest):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = payload.session_id or f"session_{timestamp}"
    safe_session_id = "".join(char for char in session_id if char.isalnum() or char in ["-", "_"])
    saved_path = SESSION_DIR / f"{safe_session_id}_{timestamp}.json"

    data = payload.dict()
    data["received_at"] = datetime.now().isoformat(timespec="seconds")

    saved_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "success": True,
        "saved_path": str(saved_path),
        "page_count": len(payload.pages),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
