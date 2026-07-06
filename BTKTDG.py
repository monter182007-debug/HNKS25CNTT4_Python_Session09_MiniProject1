from fastapi import FastAPI,status,Request,HTTPException
from pydantic import BaseModel,Field
from typing import Optional,Any
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

class BaseResponse(BaseModel):
    status_code:int
    message:str
    data:Optional[Any]
    error:Optional[str]
    timestamp: str
    path:str

class FlightCreate(BaseModel):
    flight_number :str = Field(ge=5,le=10)
    destination :str = Field(min_length=1)
    available_seats :int =Field(ge=1)

def create_response(request:Request,status_code:int,message:str,data=None,error=None):
    return BaseResponse(
        statusCode =status_code,
        message=message,
        data=data,
        error= error,
        timestamp=datetime.now().isoformat(),
        path= request.url.path
    )
flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45, "status": "scheduled", "created_at": "2026-07-01T06:00:00Z"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc", "available_seats": 12, "status": "scheduled", "created_at": "2026-07-01T07:30:00Z"}
]

@app.get("/flights")
def get_flights(
    request:Request,
    flight_status:Optional[str]=None
):
    result = flights_db
    if status:
        result=[flight for flight in result if flight["status"].lower() == flight_status.lower()]

    return create_response(request,status.HTTP_200_OK,message="Lấy danh sách chuyến bay thành công!",data=result)
        
@app.post("/flights")
def create_flights(request:Request,payload:FlightCreate):
    target_flight= next((f for f in flights_db if f["flight_number"].strip().lower() == payload.flight_number.strip().lower()),None)

    if target_flight:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    
    new_flight = payload.model_dump()

    new_flight["id"] =max([f["id"] for f in flights_db],default=0) +1

    flights_db.append(new_flight)
    return create_response(request,status.HTTP_201_CREATED,"Khởi tạo chuyến bay mới thành công!",new_flight)

@app.delete('/flights/{flight_id}')
def delete_flight(request: Request, flight_id: int):
    for i, f in enumerate(flights_db):
        if f["id"] == flight_id:
            flights_db.pop(i)
            return create_response(request, status.HTTP_200_OK, "Hủy chuyến bay thành công!")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail={
            "message": "Lỗi: Không tìm thấy mã chuyến bay yêu cầu để hủy!", 
            "error": "ERR-AIR-02: Target flight ID is missing from system scope."
        }
    )

@app.exception_handler(HTTPException)
def http_exception_handler(
    request: Request,
    exc: HTTPException
):
    response = create_response(request, exc.status_code, "Xảy ra lỗi HTTP", None, str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = create_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, "Lỗi: Dữ liệu đầu vào không hợp lệ!", None, str(exc.errors()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump()
    )

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    response = create_response(request, status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error", None, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )


