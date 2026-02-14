from fastapi import APIRouter
from app.services.uptime import uptime_seconds

router = APIRouter()

@router.get("/ping")
def ping():
    return {"pong": True}

@router.get("/uptime")
def uptime():
    return {"uptime_seconds": uptime_seconds()}
