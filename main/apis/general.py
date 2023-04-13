from fastapi import APIRouter
from main.config import settings
from pydantic import BaseModel
import main.services.k8s as k8s
import json
from typing import Optional

router = APIRouter(
    prefix="/api/v1",
    tags=["general"],
    responses={404: {"description": "Not found"}},
)


class Health(BaseModel):
    health: str

class Parameter(BaseModel):
    name: str
    value: Optional[str]
    default: Optional[str]

class Platform(BaseModel):
    id: str
    name: str
    creationDate: float
    address: str
    labels: Optional[dict]
    annotations: Optional[dict]
    parameters: Optional[list[Parameter]]
    type: str
    status: str
    namespace: str
    date: float    
    
    class Config:
        orm_mode = True


class Message(BaseModel):
    message: str 


# Status query page, can also be used for the benchmark testing 
@router.get(
    '/healthz', 
    response_model=Health,
    responses={
        404: {"model": Message, "description": "The item was not found"},
        200: {
            "description": "System information such as health status and db conenctions",
            "content": {
                "application/json": {
                    "example": {'health': 'ok'}
                }
            },
        },
    },
    tags=["general"])
async def health():
    _status = {
        "health": "ok"
    }
    return _status


# Status query page, can also be used for the benchmark testing 
@router.get(
    '/platform', 
    response_model=list[Platform],
    responses={
        404: {"model": Message, "description": "The item was not found"},
        200: {
            "description": "Platform metric set",
            "content": {
                "application/json": {
                    "example": {'id': '1234','name': 'tap-1', 'labels': 'class=foo', 'type': 'pod', 'status': 'running', 'message': 'things', 'date': '20231212'}
                }
            },
        },
    },
    tags=["general"])
async def platform():
    _resp = k8s.getMetrics()
    return _resp

