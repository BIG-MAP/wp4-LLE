from unittest import result
from fastapi import FastAPI
import pandas as pd
from pydantic import BaseModel,Field
from typing import Union
from enum import Enum

from sqlalchemy import null

d = {'A': [0.0, 0.0], 'B': [0.0, 0.0]}
df = pd.DataFrame(data = d)
print(df)
print(df.info())

class Status(Enum):
    idle = "idle"
    running = "running"
    finished = "finished"
    stopped = "stopped"

class DataLightSensor(BaseModel):    
    data: list[list[float]] = Field([], title= "The data obtained")
    dataRaw: list[list[int]] = Field([], title= "The data obtained in raw form")


class LLEOutputs(BaseModel):
    sensorResult: Union[DataLightSensor,None] = None

class Response(BaseModel):
    status: Status
    results: Union[LLEOutputs,None] = None


app = FastAPI()

@app.get("/start",response_model=Response)
def post_start():
    results = LLEOutputs(sensorResult=DataLightSensor(data=df.to_numpy().tolist(),dataRaw=df.to_numpy().tolist()))
    return Response(status=Status.finished,results=results)


