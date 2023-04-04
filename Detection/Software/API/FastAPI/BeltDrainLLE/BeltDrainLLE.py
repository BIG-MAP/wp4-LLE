#Imports
import time
from fastapi import  BackgroundTasks, FastAPI
import pandas as pd
from pydantic import BaseModel,Field
from typing import Dict, Union, List
from enum import Enum
import asyncio
from asyncio import Future
from threading import Thread



#Import drivers
from API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc #In charge of initializing pumps and valves


class Status(Enum):
    idle = "idle"
    running = "running"
    finished = "finished"
    stopped = "stopped"

def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()

# class Phase(Enum):
#     UPPER = auto()
#     LOWER = auto()
#     def getPort(self):
#         if(self == Phase.UPPER):
#             return 1
#         elif(self == Phase.LOWER):
#             return 2
#         else:
#             raise ValueError("Wrong phase")
    

class SettlingSettings(BaseModel):
    scanInterval: int = Field(20, title = "The interval for scanning", description = "The interval for scanning the funnel in seconds", gt = 0,example = 4)
    maxTime: int = Field(120, title = "", description = "The increase step for turning LEDs on", gt = 0,example = 16)

class ScanSettings(BaseModel):
    initialLEDs: int = Field(4, title = "The initial LEDs used", description = "The number of initial LEDs used", gt = 0,example = 4)
    deltaLEDs: int = Field(16, title = "The increase step", description = "The increase step for turning LEDs on", gt = 0,example = 16)
    travelDistance: int = Field(169, title = "The distance traveled in mm", description = "The distance the sensor travels from its initial position", gt = 0,le=169, example = 169)

class DetectionSettings(BaseModel):
    smoothWindowSize: int = Field(7, title = "The size of window for smoothing")
    smoothProminence: float = Field(1/15,description="The prominence used when finding peaks in the smoothed curve")
    gradient2Prominence: float = Field(1/3,description="The prominence used when finding peaks in the second gradient of the curve")

class DrainSettings(BaseModel):
    portLower: int = Field(1, title = "A port number", description = "The port number to drain the lower phase to", gt = 0, le=4, example = 1)
    portUpper: int = Field(2, title = "A port number", description = "The port number to drain the upper phase to", gt = 0, le=4, example = 1)
    mlToDrainUpper: Union[float,None] = Field(default = 500, title = "A number of ml", description = "The number of ml to drain", gt = 0, example = 100.0) 
    
class DataLightSensor(BaseModel):    
    data: list[list[float]] = Field([], title= "The data obtained")
    dataRaw: list[list[int]] = Field([], title= "The data obtained in raw form")

class DataInterface(BaseModel):
    interfaceFound: bool = Field(False,title="Has an interface been found?")
    interfacePosition: float = Field(0.0,title="The position of the interface", description= "The position of the interface in mm from the home position of the sensor")

class DataDrain(BaseModel):
    mlToDrainLower: Union[float,None] = Field(default = None, title = "A number of ml lower phase", description = "The number of ml to drain", gt = 0, example = 100.0) 
    conversionFactorLower: Union[float,None] = Field(default = None, title = "The conversion factor", description = "The calibration conversion factor from ml to seconds", example = 0.66)
    secondsLower: Union[float, None] = Field(default=None, title = "The seconds to drain", description = "The result of converting ml to seconds", example = 100.0)
    mlToDrainUpper: Union[float,None] = Field(default = None, title = "A number of ml upper phase", description = "The number of ml to drain", gt = 0, example = 100.0) 
    conversionFactorUpper: Union[float,None] = Field(default = None, title = "The conversion factor", description = "The calibration conversion factor from ml to seconds", example = 0.66)
    secondsUpper: Union[float, None] = Field(default=None, title = "The seconds to drain", description = "The result of converting ml to seconds", example = 100.0)

class DataPump(BaseModel):
    mlToPump:  Union[float,None] = Field(default = None, title = "A number of ml to pump", description = "The number of ml to pump", gt = 0, example = 100.0)
    conversionFactor:  Union[float,None] = Field(default = None, title = "The conversion factor", description = "The calibration conversion factor from ml to seconds", example = 0.66)
    secondsToPump: Union[float, None] = Field(default=None, title = "The seconds to pump", description = "The result of converting ml to seconds", example = 100.0)

class DataSettling(BaseModel):
    start: int = -1
    finish: int = -1

class LLEOutputs(BaseModel):
    sensorResult: Union[DataLightSensor,None] = None
    interfaceResult: Union[DataInterface,None] = None
    drainResult: Union[DataDrain,None] = None
    settlingResult: Union[DataSettling,None] = None
    pumpResult: Union[DataPump,None] = None

class Settings(BaseModel):
    settlingSettings: SettlingSettings = SettlingSettings()
    scanSettings: ScanSettings = ScanSettings()
    detectionSettings: DetectionSettings = DetectionSettings()
    drainSettings: DrainSettings = DrainSettings()

class Response(BaseModel):
    status: Status
    settings: Union[Settings,None] = None
    results:  Union[LLEOutputs,None] = None
    error: Union[str,None] = None

backLoop = asyncio.new_event_loop()

class LiquidExtractor:
    status: Status = Status.idle
    settings: Settings = Settings()
    results: LLEOutputs = LLEOutputs()
    error: str = ""
    runningTask: Future = None
    stopEvent = asyncio.Event()

    _loop = asyncio.get_event_loop()

    def stop(self):
        print("Stopping")
        self.stopEvent.set()
        self.runningTask.cancel()
        #print(asyncio.all_tasks(self._loop))
        LLEProc.stopPump()
        self.status = Status.stopped
        self.results = LLEOutputs()

    def startSettlingExp(self,settings):
        print("Starting settling experiment")
        self.stopEvent.clear()
        self.settings = settings
        self.status = Status.running
        #self.runningTask = self._loop.create_task(self.runDrainExp(settings))
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runSettlingExp(settings), backLoop)
        #self.runningTask = asyncio.to_thread(self.runDrainExp(settings))
        #print(asyncio.all_tasks(self._loop))

    async def runSettlingExp(self,settings):
        print("Running settling experiment")
        self.settings = settings
        self.status = Status.running
        self.results.settlingResult = DataSettling()
        self.error = ""
        elapsed = 0
        startTime = time.time()
        firstSaved = False
        count = 0
        while elapsed <= self.settings.settlingSettings.maxTime:
            current = time.time()
            elapsed = current-startTime
            print("Elapsed Time", elapsed)
            dataLight, dataLightRaw, idN, error = LLEProc.scanFunnel(self.settings.scanSettings.initialLEDs,self.settings.scanSettings.deltaLEDs,self.settings.scanSettings.travelDistance,self.stopEvent)
            if not firstSaved:
                self.results.settlingResult.start = idN
                firstSaved = True
            count += 1
            if error != "":
                self.error = self.error + ", " + error
            await asyncio.sleep(self.settings.settlingSettings.scanInterval)
        #Populate results
        self.results.settlingResult.finish = idN
        self.status = Status.finished

    def startDrainExp(self,settings):
        print("Starting drain experiment")
        self.stopEvent.clear()
        self.settings = settings
        self.status = Status.running
        #self.runningTask = self._loop.create_task(self.runDrainExp(settings))
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runDrainExp(settings), backLoop)
        #self.runningTask = asyncio.to_thread(self.runDrainExp(settings))
        #print(asyncio.all_tasks(self._loop))

    
    def startScanAndFind(self,settings):
        print("Starting scan and find")
        self.stopEvent.clear()
        self.settings = settings
        self.status = Status.running
        #self.runningTask = self._loop.create_task(self.runDrainExp(settings))
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runScanAndFind(settings), backLoop)
        #self.runningTask = asyncio.to_thread(self.runDrainExp(settings))
        #print(asyncio.all_tasks(self._loop))


    async def runScanAndFind(self,settings):
        print("Running scan and Find")
        self.error = ""
        dataLight, dataLightRaw,_, error = LLEProc.scanFunnel(self.settings.scanSettings.initialLEDs,self.settings.scanSettings.deltaLEDs,self.settings.scanSettings.travelDistance,self.stopEvent)
        #dataLight.loc[0,'A'] = 0.00
        #print(dataLight.info())
        if error != "":
            self.error = self.error + ", " + error
        interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight,self.settings.detectionSettings.smoothWindowSize,self.settings.detectionSettings.smoothProminence,self.settings.detectionSettings.gradient2Prominence)
        if error != "":
            self.error = self.error + ", " + error

        self.results.sensorResult = DataLightSensor(data = dataLight.to_numpy().tolist(),dataRaw = dataLightRaw.to_numpy().tolist())
        self.results.interfaceResult = DataInterface(interfaceFound = interfaceFound,interfacePosition = interfacePosition)
        self.status = Status.finished

    async def runDrainExp(self,settings):
        print("Running drain experiment")
        self.error = ""
        dataLight, dataLightRaw,_, error = LLEProc.scanFunnel(self.settings.scanSettings.initialLEDs,self.settings.scanSettings.deltaLEDs,self.settings.scanSettings.travelDistance,self.stopEvent)
        #dataLight.loc[0,'A'] = 0.00
        #print(dataLight.info())
        if error != "":
            self.error = self.error + ", " + error
        interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight,self.settings.detectionSettings.smoothWindowSize,self.settings.detectionSettings.smoothProminence,self.settings.detectionSettings.gradient2Prominence)
        if error != "":
            self.error = self.error + ", " + error
        if(interfaceFound):
            print("Interface Found")
            portLower, mlToDrainLower, conversionFactorLower, secondsToDrainLower, error = await LLEProc.drainLowerPhase(self.settings.drainSettings.portLower,interfacePosition)
            if error != "":
                self.error = self.error + ", " + error
            portUpper, mlToDrainUpper, conversionFactorUpper, secondsToDrainUpper, error = await LLEProc.drainUpperPhase(self.settings.drainSettings.portUpper)
            if error != "":
                self.error = self.error + ", " + error

            #Populate results

            self.results.sensorResult = DataLightSensor(data = dataLight.to_numpy().tolist(),dataRaw = dataLightRaw.to_numpy().tolist())
            self.results.interfaceResult = DataInterface(interfaceFound = interfaceFound,interfacePosition = interfacePosition)
            self.results.drainResult = DataDrain(mlToDrainLower = mlToDrainLower,conversionFactorLower= conversionFactorLower,secondsLower=secondsToDrainLower,mlToDrainUpper=mlToDrainUpper,conversionFactorUpper=conversionFactorUpper,secondsUpper=secondsToDrainUpper)    
            self.status = Status.finished
        else:
            print("Interface not found")
            dataLight[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]] = dataLight[["A","B","C","D","E","F","G","H","I","J","K","L","R","S","T","U","V","W"]].apply(pd.to_numeric)
            self.results.sensorResult = DataLightSensor(data = dataLight.to_numpy().tolist(),dataRaw = dataLightRaw.to_numpy().tolist())
            print(self.results.sensorResult)
            self.results.interfaceResult = DataInterface(interfaceFound = interfaceFound,interfacePosition = interfacePosition)
            self.results.drainResult = DataDrain()    
            self.status = Status.finished

    def returnSensorData(self,idN: int):
        print("Returning sensor data with id: "+str(idN))
        df = LLEProc.getSensorData(idN)
        dfRaw = LLEProc.getSensorDataRaw(idN)
        return df, dfRaw

    def startDrainToPort(self,ml,port):
        print("Starting drain experiment")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runDrainMlToPort(ml,port), backLoop)

    async def runDrainMlToPort(self,ml,port):
        print("Running drain ml to port")
        portDrained, mlToDrain, conversionFactor, secondsToDrain, error = await LLEProc.drainMlToPort(ml,port)
        self.results.drainResult = DataDrain(mlToDrainLower = mlToDrain,conversionFactorLower= conversionFactor,secondsLower=secondsToDrain)
        self.status = Status.finished

    def startPumpFromPort(self,ml,port):
        print("Starting pump")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runPumpMlFromPort(ml,port), backLoop)

    async def runPumpMlFromPort(self,ml,port):
        print("Running pump ml from port")
        portPumped, mlToPump, conversionFactor, secondsToPump, error = await LLEProc.pumpMlFromPort(ml,port,0)
        self.results.pumpResult = DataPump(mlToPump= mlToPump,conversionFactor = conversionFactor,secondsToPump=secondsToPump)
        self.status = Status.finished


#Create app
app = FastAPI()

extractor = LiquidExtractor()


@app.on_event("startup")
async def startup_event():
    t = Thread(target=start_background_loop, args=(backLoop,), daemon=True)
    t.start()

#Endpoints

#Get /
#Get the basic information from the server
@app.get("/")
async def rootPath():
    return {"name": "LLE",
            "Device id": 1}


#Get LLE Drain request
@app.get("/start/Drain",response_model=Response)
async def do_DrainRun(background_tasks: BackgroundTasks):
    settings = Settings()
    background_tasks.add_task(extractor.startDrainExp,settings)
    return Response(status=extractor.status, settings=extractor.settings)
    
@app.post("/start/Drain",response_model=Response)
def post_start(settings: Settings,background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startDrainExp,settings)
    return Response(status=extractor.status, settings=extractor.settings)

@app.get("/status",response_model=Response)
def get_status():
    return Response(status=extractor.status, settings=extractor.settings)

@app.get("/stop",response_model=Response)
def do_stop():
    extractor.stop()
    return Response(status=extractor.status, settings=extractor.settings,error=extractor.error)

@app.get("/results",response_model=Response)
def get_results():
    return Response(status=extractor.status, settings=extractor.settings, results=extractor.results,error=extractor.error)

#LLE Settling requests
@app.get("/start/Settling",response_model=Response)
async def do_Settling_Run(background_tasks: BackgroundTasks):
    settings = Settings()
    background_tasks.add_task(extractor.startSettlingExp,settings)
    return Response(status=extractor.status, settings=extractor.settings)
    
@app.post("/start/Settling",response_model=Response)
def post_Settling_start(settings: Settings,background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startSettlingExp,settings)
    return Response(status=extractor.status, settings=extractor.settings)

#Get /imageData Procedures
@app.get("/sensorData/{item_id}",response_model=Response)
def getSensorData(item_id: int):
    df, dfRaw = extractor.returnSensorData(item_id)
    return Response(status=extractor.status,results=LLEOutputs(sensorResult=DataLightSensor(data=df.to_numpy().tolist(),dataRaw=dfRaw.to_numpy().tolist())))

#Get /imageData Procedures
@app.get("/drainToPort/{port}/{ml}",response_model=Response)
def get_drainToPort(port: int, ml: float,background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startDrainToPort,ml,port)
    return Response(status=extractor.status, settings=extractor.settings)

#Get /imageData Procedures
@app.get("/pumpFromPort/{port}/{ml}",response_model=Response)
def get_pumpFromPort(port: int, ml: float,background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startPumpFromPort,ml,port)
    return Response(status=extractor.status, settings=extractor.settings)

#LLE Scan and Find requests
@app.get("/start/ScanFind",response_model=Response)
async def do_ScanFind_Run(background_tasks: BackgroundTasks):
    settings = Settings()
    background_tasks.add_task(extractor.startScanAndFind,settings)
    return Response(status=extractor.status, settings=extractor.settings)

#Get /imageData Procedures
@app.get("/imageData/{id}")
async def getImageData(id: int):
    pass
    # imageFolderPath = await LLEProc.getImageData()
    # return {"imageData": returnJson}
#Get the last image data obtained when scanning the interface

