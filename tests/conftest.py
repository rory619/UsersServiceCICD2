import pytest 
from fastapi.testclient import TestClient 
from sqlalchemy import create_engine, event 
from sqlalchemy.orm import sessionmaker 
 
import app.database as database
import app.models as models 


 
# In-memory SQLite, shared across threads 
TEST_DB_URL = "sqlite+pysqlite:///./test_users.db"

engine = create_engine(TEST_DB_URL,connect_args={"check_same_thread": False},)
 
@event.listens_for(engine, "connect") 
def _fk_on(dbapi_conn, _): 
    dbapi_conn.execute("PRAGMA foreign_keys=ON") 



connection = engine.connect()
 
TestingSessionLocal = sessionmaker(bind=connection, expire_on_commit=False,  autocommit=False, autoflush=False) 

database.engine = engine
database.SessionLocal = TestingSessionLocal

from app.main import app  
 
@pytest.fixture(autouse=True) 
def _schema(): 
    models.Base.metadata.create_all(bind=connection) 
    yield 
    models.Base.metadata.drop_all(bind=connection) 
 
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