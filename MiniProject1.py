from fastapi import FastAPI,HTTPException,status,Request
from pydantic import BaseModel,Field
from typing import Optional,List
from datetime import datetime 
from enum import Enum
import re 
app = FastAPI()

class TaskCreateSchema(BaseModel):
    title :str = Field(min_length=3, max_length=150,description="Tiêu đề từ 3-150 ký tự")
    description :str = Field(description="Mô tả công việc")
    assignee :str = Field(min_length=2, description="Tên người nhận việc tối thiểu 2 ký tự")
    priority :int = Field(ge=1, le=5, description="Độ ưu tiên từ 1 đến 5")

class TaskUpdateSchema(BaseModel):
    title :str = Field(min_length=3, max_length=150,description="Tiêu đề từ 3-150 ký tự")
    description :str = Field(description="Mô tả công việc")
    assignee :str = Field(min_length=2, description="Tên người nhận việc tối thiểu 2 ký tự")
    priority :int = Field(ge=1, le=5, description="Độ ưu tiên từ 1 đến 5")
    status: TaskStatus

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPublicResponse(BaseModel):
    id: int
    title: str
    description: str
    assignee: str
    priority: int
    status: str
    created_at: str

tasks_db = [
    {
        "id": 1,
        "title": "Thiết kế cơ sở dữ liệu Shop AI",
        "description": "Xây dựng các lưu trữ bảng.",
        "assignee": "QuyDev",
        "priority": 1,
        "status": "todo",
        "created_at": "2026-07-01T09:50:00Z",
        "internal_notes": "Lưu ý bảo mật"
    }
]

# API 1
@app.get('/tasks',response_model=list[TaskPublicResponse],status_code=status.HTTP_200_OK)
def get_tasks():
    return tasks_db
@app.get("/tasks/search")
def get_tasks(
    keyword:Optional[str]=None,
    status:Optional[str]=None
):

    result = tasks_db
    if keyword:
        pattern=re.compile(keyword,re.IGNORECASE)
        result=[task for task in result if pattern.search(task["title"]) or pattern.search(task["assignee"])]

    if status:
        result = [task for task in result if task["status"] == status]

    return {
        "total":len(result),
        "data":result
    }

@app.post("/tasks",response_model=TaskPublicResponse,status_code=status.HTTP_201_CREATED)
def create_tasks(payload:TaskCreateSchema):
    new_tasks= payload.model_dump()

    new_tasks["id"] = max([task["id"] for task in tasks_db],default=0)+1

    new_tasks["status"] = TaskStatus.TODO.value
    new_tasks["created_at"] = datetime.now().isoformat()
    new_tasks["internal_notes"] = ""

    tasks_db.append(new_tasks)

@app.get("/tasks/{task_id}",status_code=status.HTTP_200_OK)
def get_tasks_by_id(task_id:int):

    target_task = next((task for task in tasks_db if task["id"] == task_id),None)

    if not target_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy công việc"
        )
    
    return target_task

@app.put("/tasks/{task_id}",status_code=status.HTTP_200_OK)
def update_tasks(task_id:int,payload:TaskUpdateSchema):
    target_task = next((t for t in tasks_db if t["id"] == task_id), None)
    
    if not target_task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    
    update_data = payload.model_dump()
    update_data["id"] = task_id
    target_task.update(update_data)

    return target_task

@app.delete("/tasks/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
def del_tasks(task_id:int):
    target_task = next((t for t in tasks_db if t["id"] == task_id), None)
    
    if not target_task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")
    
    tasks_db.remove(target_task)
    return


