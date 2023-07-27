import time
import os
from enum import Enum
import uvicorn
from fastapi import  FastAPI
from pydantic import BaseModel,Field


from software.Drivers.DiaphragmPumpCmd import DiaphragmPumpCmdDriver as PumpDriver


class Status(Enum):
    stopped = "stopped"
    running = "running"


class PumpSettings(BaseModel):
    speed: int = Field(0, title = "The pump speed", ge = 0, le = 4095, example = 1024)
    run: bool = Field(False, title = "Start the pump", description = "Starts or stops the pump regardless of speed")

class StatusResponse(BaseModel):
    status: Status

class DiaphragmPump:
    status: Status = Status.stopped
    settings: PumpSettings = PumpSettings()

    def startPump(self):
        self.settings.run = True
        self.status = Status.running
        if(PumpDriver.getPumpState()):
            print("Pump already started")
        else:
            PumpDriver.cyclePump()
            print("Pump started")

    def stopPump(self):
        if(PumpDriver.getPumpState()):
            PumpDriver.stopPump()
            self.settings.run = False
            self.settings.speed = 0
            self.status = Status.stopped
        print("Pump stopped")


    def setSpeed(self,speed:int):
        self.settings.speed = speed
        PumpDriver.setVoltage(speed)
        print("Pump speed set to " + str(speed))


    def set(self,settings:PumpSettings):
        self.settings = settings
        PumpDriver.setVoltage(settings.speed)
        print("Pump speed set to " + str(settings.speed))
        
        if(settings.run):
            if(not PumpDriver.getPumpState()):
                PumpDriver.cyclePump()
                print("Pump started")
            self.status = Status.running
        else:
            if(PumpDriver.getPumpState()):
                PumpDriver.stopPump()
                print("Pump stopped")
            self.status = Status.stopped
            



        




#Create app
app = FastAPI()
pump = DiaphragmPump()

#Get /
#Get the basic information from the server
@app.get("/")
async def rootPath():
    return {"name": "Diaphragm Pump",
            "Device id": 2}

@app.get("/stop",response_model=StatusResponse)
def do_stop():
    pump.stopPump()
    return StatusResponse(status=pump.status)

@app.get("/start",response_model=StatusResponse)
async def do_start():
    pump.startPump()
    return StatusResponse(status=pump.status)


@app.get("/setSpeed/{speed}",response_model=StatusResponse)
async def do_setSpeed(speed: int):
    pump.setSpeed(speed)
    return StatusResponse(status=pump.status)

@app.post("/set",response_model=StatusResponse)
async def do_run(settings: PumpSettings):
    pump.set(settings)
    return StatusResponse(status=pump.status)

def main():
    uvicorn.run("software.API.FastAPI.DiaphragmPumpLLE.DiaphragmPumpLLE:app", host='0.0.0.0', port=8000)

if __name__ == "__main__":
    main()
