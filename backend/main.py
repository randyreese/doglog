from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import socket as _socket, io as _io
from alembic.config import Config
from alembic import command
import models  # noqa: F401
from routers import dogs, events, status, health, meals, milestones, meal_configs, medications, medication_logs


def _run_migrations():
    from sqlalchemy import inspect as sa_inspect
    from database import engine, Base

    alembic_cfg = Config(Path(__file__).parent / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(Path(__file__).parent / "alembic"))

    if not sa_inspect(engine).has_table("dogs"):
        from sqlalchemy import text
        from alembic.script import ScriptDirectory
        head = ScriptDirectory.from_config(alembic_cfg).get_current_head()
        Base.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS alembic_version "
                "(version_num VARCHAR(32) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            ))
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:rev)"), {"rev": head})
    else:
        command.upgrade(alembic_cfg, "head")


_run_migrations()


def _seed_dogs():
    from database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(models.Dog).count() == 0:
            db.add(models.Dog(name="Tess", active=True, track_pee=True))
            db.add(models.Dog(name="Pickles", active=True, track_pee=False))
            db.commit()
    finally:
        db.close()


_seed_dogs()


def _prune_old_events():
    from database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text(
            "DELETE FROM pee_poo_events WHERE timestamp < datetime('now', '-7 days')"
        ))
        db.commit()
    finally:
        db.close()


_prune_old_events()


app = FastAPI(
    title="Doglog API",
    description="Dog care tracking backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dogs.router, prefix="/doglog")
app.include_router(events.router, prefix="/doglog")
app.include_router(status.router, prefix="/doglog")
app.include_router(health.router, prefix="/doglog")
app.include_router(meals.router, prefix="/doglog")
app.include_router(milestones.router, prefix="/doglog")
app.include_router(meal_configs.router, prefix="/doglog")
app.include_router(medications.router, prefix="/doglog")
app.include_router(medication_logs.router, prefix="/doglog")


from datetime import datetime as _dt
_START_TIME = _dt.now()


@app.get("/doglog/health")
def health():
    return {"status": "ok"}


@app.get("/doglog/version")
def version():
    return {"app": "doglog", "started_at": _START_TIME.isoformat()}


def _lan_ip() -> str:
    s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


@app.get("/doglog/lan-url")
def lan_url():
    return {"url": f"http://{_lan_ip()}:8001"}


@app.get("/doglog/connect-qr")
def connect_qr():
    import qrcode
    url = f"https://mint.local/doglog"
    img = qrcode.make(url)
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


_pwa_dist = Path(__file__).parent.parent / "mobile" / "dist"
if _pwa_dist.exists():
    app.mount("/doglog", StaticFiles(directory=_pwa_dist, html=True), name="pwa")
