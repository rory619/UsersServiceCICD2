import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base


engine = create_engine("sqlite+pysqlite:///:memory:",connect_args={"check_same_thread": False},poolclass=StaticPool,)

TestingSessionLocal = sessionmaker(bind=engine,autocommit=False,autoflush=False,expire_on_commit=False,)

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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def _create_user(client, *, name="Paul", email="pl@atu.ie", age=25, student_id="S1234567"):
    return client.post("/api/users",json={"name": name, "email": email, "age": age, "student_id": student_id},)

def test_create_user(client):
    r = _create_user(client)
    assert r.status_code == 201
    assert r.json()["email"] == "pl@atu.ie"

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_greet(client):
    r = client.get("/api/greet/Rory")
    assert r.status_code == 200
    assert "Rory" in r.json()["message"]

def test_list_users(client):
    _create_user(client)
    r = client.get("/api/users")
    assert r.status_code == 200
    assert len(r.json()) == 1

def test_get_user_404(client):
    r = client.get("/api/users/999")
    assert r.status_code == 404

def test_update_user_404(client):
    r = client.put("/api/users/999",json={"name": "X", "email": "x@atu.ie", "age": 20, "student_id": "S0000000"},)
    assert r.status_code == 404

def test_delete_user_flow(client):
    r = _create_user(client, email="del@atu.ie", student_id="S1111111")

    user_id = r.json()["id"]

    r2 = client.delete(f"/api/users/{user_id}")
    assert r2.status_code == 204

    r3 = client.get(f"/api/users/{user_id}")
    assert r3.status_code == 404