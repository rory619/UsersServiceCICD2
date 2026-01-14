from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base

from fastapi import Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import UsersDB
from app.schemas import UserCreate, UserRead, UserUpdate


# Replacing @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
# CORS (add this block)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-friendly; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/greet/{name}")
def greet(name: str):
    return {"message": f"Hello, {name} from Service A!"}


# Users
@app.post(
    "/api/users", response_model=UserRead, status_code=201, summary="Create new user"
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    db_user = UsersDB(**payload.model_dump())
    db.add(db_user)
    commit_or_rollback(db, "User create failed")
    db.refresh(db_user)
    return db_user


@app.get("/api/users", response_model=list[UserRead])
def list_users(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(UsersDB).order_by(UsersDB.id).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@app.get(
    "/api/users/{user_id}",
    response_model=UserRead,
    summary="Get a single user",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(UsersDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/api/users/{user_id}", response_model=UserRead, summary="Update an existing user")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(UsersDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)

    commit_or_rollback(db, "User update failed")
    db.refresh(user)
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> Response:
    user = db.get(UsersDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
