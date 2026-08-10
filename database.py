from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# IPv4 Pooler URL mapped directly to your Supabase project
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.hviixeshviiaommduejd:Mohanlos0204@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()