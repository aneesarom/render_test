from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.supabase.supabase_client import supabase
from app.auth.jwt_handler import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreateRequest(BaseModel):
    title: str
    total_minutes: float
    description: str

class TaskUpdateRequest(BaseModel):
    title: str
    status: str
    description: str
    total_minutes: float


@router.post("/create")
def create_task(task: TaskCreateRequest, current_user: dict = Depends(get_current_user)):
    
    res = supabase.table("tasks").insert({
        "title": task.title,
        "status": "created",
        "description": task.description,
        "total_minutes": task.total_minutes
    }).execute()

    if not res.data:
        raise HTTPException(status_code=400, detail="Task creation failed")

    return res.data[0]


@router.get("/list")
def list_tasks(current_user: dict = Depends(get_current_user)):
    res = supabase.table("tasks").select("*").execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="No tasks found")

    return res.data


@router.get("/{task_id}")
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    res = supabase.table("tasks").select("*").eq("id", task_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")

    return res.data[0]

@router.put("/update/{task_id}")
def update_task(task_id: int, task: TaskUpdateRequest, current_user: dict = Depends(get_current_user)):
    update_data = {
        "title": task.title,
        "status": task.status,
        "total_minutes": task.total_minutes,
        "description": task.description
    }

    res = supabase.table("tasks").update(update_data).eq("id", task_id).execute()

    if not res.data:
        raise HTTPException(status_code=400, detail="Task update failed")

    return res.data[0]

@router.delete("/delete/{task_id}")
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    res = supabase.table("tasks").delete().eq("id", task_id).execute()

    if not res.data:
        raise HTTPException(status_code=400, detail="Task deletion failed")

    return {"detail": "Task deleted successfully"}