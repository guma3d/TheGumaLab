import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL로의 전환을 대비한 깔끔한 환경변수 설정
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:////app/data/gumaphoto_main.db")

# SQLite 전용 옵션 (PostgreSQL 사용 시에는 이 옵션이 필요 없습니다)
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
