import pytest 
from fastapi.testclient import TestClient 
from sqlalchemy import create_engine, event 
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.pool import StaticPool 
 
from app.main import app 
import app.database as database
from app.models import Base, UsersDB # noqa: F401


 
# In-memory SQLite, shared across threads 
engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool) 
 
@event.listens_for(engine, "connect") 
def _fk_on(dbapi_conn, _): 
    dbapi_conn.execute("PRAGMA foreign_keys=ON") 
 
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False) 
database.engine = engine
database.SessionLocal = TestingSessionLocal
 
@pytest.fixture(autouse=True) 
def _schema(): 
    Base.metadata.create_all(bind=engine) 
    yield 
    Base.metadata.drop_all(bind=engine) 
 
@pytest.fixture 
def client(): 
    def override_get_db(): 
        db = TestingSessionLocal() 
        try: 
            yield db 
        finally: 
            db.close() 
    app.dependency_overrides[database.get_db] = override_get_db 
    with TestClient(app) as c: 
        yield c 
    app.dependency_overrides.clear()
