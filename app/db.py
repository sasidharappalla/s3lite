import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def wait_for_db(max_attempts: int = 30, sleep_s: float = 1.0) -> None:
    last_exc = None
    for _ in range(max_attempts):
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return
        except Exception as exc:
            last_exc = exc
            time.sleep(sleep_s)
    raise RuntimeError(f"Database not ready after {max_attempts} attempts: {last_exc}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
