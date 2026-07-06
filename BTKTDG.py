from fastapi import FastAPI, status, HTTPException, Request
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

class BaseResponse(BaseModel):
    statusCode: int     
    message: str        
    data: Optional[Any] = None
    error: Optional[Any] = None
    timestamp: str
    path: str

class CreateFlight(BaseModel):
    flight_number: str = Field(min_length=5, max_length=10)
    destination: str = Field(min_length=1)
    available_seats: int = Field(ge=1)

def create_response(request: Request, status_code: int, message: str, data=None, error=None):
    return BaseResponse(
        statusCode=status_code,
        message=message,
        data=data,
        error=error,
        timestamp=datetime.now().isoformat(),
        path=request.url.path
    )

flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45, "status": "scheduled", "created_at": "2026-07-01T06:00:00Z"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc", "available_seats": 12, "status": "scheduled", "created_at": "2026-07-01T07:30:00Z"}
]

@app.get('/flights')
def get_flights(request: Request, flight_status: Optional[str] = None):
    if flight_status:
        filtered_flights = [f for f in flights_db if f["status"] == flight_status]
    else:
        filtered_flights = flights_db

    return create_response(request, status.HTTP_200_OK, "Lấy danh sách chuyến bay thành công!", data=filtered_flights)

@app.post('/flights', status_code=status.HTTP_201_CREATED)
def create_flight(request: Request, flight: CreateFlight):
    target_flight = next((f for f in flights_db if f['flight_number'].upper() == flight.flight_number.upper()), None)

    if target_flight:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Lỗi: Số hiệu chuyến bay này đã tồn tại trên hệ thống điều hành!",
                "error": "ERR-AIR-01: Flight number conflict in current active schedule database."
            }
        )

    new_id = max([f["id"] for f in flights_db], default=0) + 1
    new_flight = {
        "id": new_id,
        "flight_number": flight.flight_number,
        "destination": flight.destination,
        "available_seats": flight.available_seats,
        "status": "scheduled",
        "created_at": datetime.now().isoformat()
    }
    flights_db.append(new_flight)
    return create_response(request, status.HTTP_201_CREATED, "Khởi tạo chuyến bay mới thành công!", data=new_flight)

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
