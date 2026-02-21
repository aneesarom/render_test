from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from app.auth.dependencies import get_current_user
from app.metrics import metrics_store

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def metrics(current_user: dict = Depends(get_current_user)):    
    return JSONResponse(content=metrics_store.get_metrics())