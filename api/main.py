from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import router

settings = get_settings()

app = FastAPI(
    title="Luxury Vintage Bag Price API",
    version="1.0.0",
    description="Price tracking and analytics for luxury vintage handbags",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
