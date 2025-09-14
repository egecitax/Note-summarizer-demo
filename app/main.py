import asyncio
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import SessionLocal, Base, engine
from app.models import User, Role, Note, NoteStatus
from app.password import hash_password, verify_password
from app.JWT import create_token, decode_token
from app.summarizer import summarize

app = FastAPI(title="Notes API")
security = HTTPBearer()

# -----------------------
# Auth helpers
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    data = decode_token(creds.credentials)  # {"sub": email, "role": ...}
    email = data["sub"]
    u = db.query(User).filter(User.email == email).first()
    if not u:
        raise HTTPException(401, "Unauthorized")
    return u

# -----------------------
# Background worker (queue)
# -----------------------
queue: asyncio.Queue[int] = asyncio.Queue()

async def worker():
    while True:
        note_id = await queue.get()
        db: Session = SessionLocal()
        note = None
        try:
            note = db.query(Note).get(note_id)
            if not note:
                queue.task_done()
                continue

            note.status = NoteStatus.processing
            db.commit()
            db.refresh(note)

            # Local/HF summarizer
            note.summary = summarize(note.raw_text)
            note.status = NoteStatus.done
            db.commit()
        except Exception:
            if note:
                note.status = NoteStatus.failed
                db.commit()
        finally:
            db.close()
            queue.task_done()

# -----------------------
# Lifecycle
# -----------------------
@app.on_event("startup")
def startup():
    # tabloların varlığını garanti et
    Base.metadata.create_all(bind=engine)
    # worker'ı başlat
    asyncio.create_task(worker())

# -----------------------
# Health / root
# -----------------------
@app.get("/")
def root():
    return {"ok": True, "message": "Notes API up"}

@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------
# Auth endpoints
# -----------------------
@app.post("/auth/signup")
def signup(email: str, password: str, role: str = "AGENT", db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email exists!")
    try:
        user = User(email=email, password_hash=hash_password(password), role=Role(role))
    except ValueError:
        raise HTTPException(422, "Role must be ADMIN or AGENT")

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.email, user.role.value), "token_type": "bearer"}

@app.post("/auth/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == email).first()
    if not u or not verify_password(password, u.password_hash):
        raise HTTPException(401, "Invalid Credentials!")
    return {"access_token": create_token(u.email, u.role.value), "token_type": "bearer"}

# -----------------------
# Admin test
# -----------------------
@app.get("/admin/ping")
def admin_ping(user: User = Depends(get_current_user)):
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Admins Only")
    return {"ok": True, "who": user.email, "role": user.role.value}

class NoteIn(BaseModel):
    raw_text: str

@app.post("/notes")
async def create_note(body: NoteIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = Note(owner_id=user.id, raw_text=body.raw_text, status=NoteStatus.queued)
    db.add(note); db.commit(); db.refresh(note)
    await queue.put(note.id)
    return {
        "id": note.id,
        "owner_id": note.owner_id,
        "raw_text": note.raw_text,
        "status": note.status.value,
        "summary": note.summary,
    }

@app.get("/notes/{note_id}")
def get_note(note_id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    note = db.query(Note).get(note_id)
    if not note:
        raise HTTPException(404,"Not Found")

    if user.role != Role.ADMIN and note.owner_id != user.id:
        raise HTTPException(403,"Forbidden!")

    return {
        "id":note.id,
        "owner_id": note.owner_id,
        "raw_text": note.raw_text,
        "status":note.status.value,
        "summary": note.summary
    }

