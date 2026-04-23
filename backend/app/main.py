import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.database import Base, engine
from app.routers.expenses import router as expenses_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Expense Tracker API", version="1.0.0", lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    detail = errors[0]["msg"] if errors else "Validation error"
    return JSONResponse(
        status_code=422,
        media_type="application/problem+json",
        content={
            "type": "https://httpstatuses.com/422",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": detail,
        },
    )


app.include_router(expenses_router)
