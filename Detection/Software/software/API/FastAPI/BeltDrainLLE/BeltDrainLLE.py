# Imports
import time
import os
from fastapi import BackgroundTasks, FastAPI, Response
import pandas as pd
from pydantic import BaseModel, Field
from typing import Dict, Union, List
from enum import Enum
import asyncio
from asyncio import Future
from threading import Thread
import zipfile
from io import BytesIO
import uvicorn
from datetime import datetime
import logging

# Import drivers
from software.API.FastAPI.BeltDrainLLE import \
    LLEBeltDrainProcedures as LLEProc  # In charge of initializing pumps and valves

# Sitting up locking to info level
logging.basicConfig(level=logging.INFO)


class Status(Enum):
    idle = "idle"
    running = "running"
    finished = "finished"
    stopped = "stopped"
    error = "error"


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
    scanInterval: int = Field(20, title="The interval for scanning",
                              description="The interval for scanning the funnel in seconds", gt=0, example=4)  # 300
    settlingTime: int = Field(120, title="", description="The time lapse for settling in seconds", gt=0,
                              example=16)  # 3600


class ScanSettings(BaseModel):
    initialLEDs: int = Field(4, title="The initial LEDs used", description="The number of initial LEDs used", gt=0,
                             example=4)
    deltaLEDs: int = Field(16, title="The increase step", description="The increase step for turning LEDs on", gt=0,
                           example=16)
    travelDistance: int = Field(169, title="The distance traveled in mm",
                                description="The distance the sensor travels from its initial position", gt=0, le=169,
                                example=169)


class DetectionSettings(BaseModel):
    smoothWindowSize: int = Field(7, title="The size of window for smoothing")
    smoothProminence: float = Field(1 / 15, description="The prominence used when finding peaks in the smoothed curve")
    gradient2Prominence: float = Field(1 / 3,
                                       description="The prominence used when finding peaks in the second gradient of the curve")


class DrainSettings(BaseModel):
    portLower: int = Field(1, title="A port number", description="The port number to drain the lower phase to", gt=0,
                           le=4, example=1)
    portUpper: int = Field(2, title="A port number", description="The port number to drain the upper phase to", gt=0,
                           le=4, example=1)
    mlToDrainUpper: Union[float, None] = Field(default=500, title="A number of ml",
                                               description="The number of ml to drain", gt=0, example=100.0)
    useTubingSensor: bool = Field(default=True, title="Enable the tubing sensor at the output",
                                  description="Enable the use of the tubing sensor at the output of the funnel as a"
                                              "redundant sensor to stop draining of the lower phase")


class Settings(BaseModel):
    settlingSettings: SettlingSettings = SettlingSettings()
    scanSettings: ScanSettings = ScanSettings()
    detectionSettings: DetectionSettings = DetectionSettings()
    drainSettings: DrainSettings = DrainSettings()


class DataLightSensor(BaseModel):
    data: list[list[float]] = Field([], title="The data obtained")
    dataRaw: list[list[int]] = Field([], title="The data obtained in raw form")


class DataInterface(BaseModel):
    interfaceFound: bool = Field(False, title="Has an interface been found?")
    interfacePosition: float = Field(0.0, title="The position of the interface",
                                     description="The position of the interface in mm from the home position of the sensor")
    lastScanTime: Union[datetime, None] = Field(None, title="The time of the last scan")


class DataDrain(BaseModel):
    mlToDrainLower: Union[float, None] = Field(default=None, title="A number of ml lower phase",
                                               description="The number of ml to drain", example=100.0)
    conversionFactorLower: Union[float, None] = Field(default=None, title="The conversion factor",
                                                      description="The calibration conversion factor from ml to seconds",
                                                      example=0.66)
    secondsLower: Union[float, None] = Field(default=None, title="The seconds to drain",
                                             description="The result of converting ml to seconds", example=100.0)
    mlToDrainUpper: Union[float, None] = Field(default=None, title="A number of ml upper phase",
                                               description="The number of ml to drain", example=100.0)
    conversionFactorUpper: Union[float, None] = Field(default=None, title="The conversion factor",
                                                      description="The calibration conversion factor from ml to seconds",
                                                      example=0.66)
    secondsUpper: Union[float, None] = Field(default=None, title="The seconds to drain",
                                             description="The result of converting ml to seconds", example=100.0)


class DataPump(BaseModel):
    mlToPump: Union[float, None] = Field(default=None, title="A number of ml to pump",
                                         description="The number of ml to pump", gt=0, example=100.0)
    conversionFactor: Union[float, None] = Field(default=None, title="The conversion factor",
                                                 description="The calibration conversion factor from ml to seconds",
                                                 example=0.66)
    secondsToPump: Union[float, None] = Field(default=None, title="The seconds to pump",
                                              description="The result of converting ml to seconds", example=100.0)


class DataSettling(BaseModel):
    start: int = -1
    finish: int = -1


class LLEOutputs(BaseModel):
    sensorResult: Union[DataLightSensor, None] = None
    interfaceResult: Union[DataInterface, None] = None
    drainResult: Union[DataDrain, None] = None
    settlingResult: Union[DataSettling, None] = None
    pumpResult: Union[DataPump, None] = None


class ResultsResponse(BaseModel):
    status: Status
    results: Union[LLEOutputs, None] = None
    error: Union[str, None] = None


class StatusResponse(BaseModel):
    status: Status


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
        # print(asyncio.all_tasks(self._loop))
        LLEProc.stopPump()
        self.status = Status.stopped
        self.results = LLEOutputs()

    def startSettlingExp(self, settings):
        print("Starting settling experiment")
        self.stopEvent.clear()
        self.settings = settings
        self.status = Status.running
        # self.runningTask = self._loop.create_task(self.runDrainExp(settings))
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runSettlingExp(), backLoop)
        # self.runningTask = asyncio.to_thread(self.runDrainExp(settings))
        # print(asyncio.all_tasks(self._loop))

    async def runSettlingExp(self):
        print("Running settling experiment")
        self.status = Status.running
        self.results.settlingResult = DataSettling()
        self.results.interfaceResult = DataInterface()
        self.error = ""
        elapsed = 0
        startTime = time.time()
        firstSaved = False
        count = 0
        while elapsed <= self.settings.settlingSettings.settlingTime:
            current = time.time()
            elapsed = current - startTime
            print("Elapsed Time", elapsed)
            dataLight, dataLightRaw, idN, error = LLEProc.scanFunnel(self.settings.scanSettings.initialLEDs,
                                                                     self.settings.scanSettings.deltaLEDs,
                                                                     self.settings.scanSettings.travelDistance,
                                                                     self.stopEvent)
            self.results.interfaceResult.lastScanTime = datetime.now()
            if not firstSaved:
                self.results.settlingResult.start = idN
                firstSaved = True
            count += 1
            if error != "":
                self.error = self.error + ", " + error
            await asyncio.sleep(self.settings.settlingSettings.scanInterval)
        # Populate results
        self.results.settlingResult.finish = idN
        self.status = Status.finished

    def startDrainExp(self, lType, settings):
        print("Starting drain experiment")
        self.stopEvent.clear()
        self.settings = settings
        self.status = Status.running
        # self.runningTask = self._loop.create_task(self.runDrainExp(settings))
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runDrainExp(lType), backLoop)
        # self.runningTask = asyncio.to_thread(self.runDrainExp(settings))
        # print(asyncio.all_tasks(self._loop))

    async def runDrainExp(self, lType):
        print("Running drain experiment")
        self.error = ""

        LLEProc.setLiquidType(lType)

        dataLight, dataLightRaw, _, error = LLEProc.scanFunnel(self.settings.scanSettings.initialLEDs,
                                                               self.settings.scanSettings.deltaLEDs,
                                                               self.settings.scanSettings.travelDistance,
                                                               self.stopEvent)
        # dataLight.loc[0,'A'] = 0.00
        # print(dataLight.info())
        if error != "":
            self.error = self.error + ", " + error
        interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight,
                                                                         self.settings.detectionSettings.smoothWindowSize,
                                                                         self.settings.detectionSettings.smoothProminence,
                                                                         self.settings.detectionSettings.gradient2Prominence)
        if error != "":
            self.error = self.error + ", " + error
        if (interfaceFound):
            print("Interface Found")
            portLower, mlToDrainLower, conversionFactorLower, secondsToDrainLower, error = await LLEProc.drainLowerPhase(
                self.settings.drainSettings.portLower, interfacePosition, self.settings.drainSettings.useTubingSensor)
            if error != "":
                self.error = self.error + ", " + error
            portUpper, mlToDrainUpper, conversionFactorUpper, secondsToDrainUpper, error = await LLEProc.drainUpperPhase(
                self.settings.drainSettings.portUpper)
            if error != "":
                self.error = self.error + ", " + error

            # Populate results

            self.results.sensorResult = DataLightSensor(data=dataLight.to_numpy().tolist(),
                                                        dataRaw=dataLightRaw.to_numpy().tolist())
            self.results.interfaceResult = DataInterface(interfaceFound=interfaceFound,
                                                         interfacePosition=interfacePosition,
                                                         lastScanTime=datetime.now())
            self.results.drainResult = DataDrain(mlToDrainLower=mlToDrainLower,
                                                 conversionFactorLower=conversionFactorLower,
                                                 secondsLower=secondsToDrainLower, mlToDrainUpper=mlToDrainUpper,
                                                 conversionFactorUpper=conversionFactorUpper,
                                                 secondsUpper=secondsToDrainUpper)
            self.status = Status.finished
        else:
            print("Interface not found")
            dataLight[["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "R", "S", "T", "U", "V", "W"]] = \
            dataLight[["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "R", "S", "T", "U", "V", "W"]].apply(
                pd.to_numeric)
            self.results.sensorResult = DataLightSensor(data=dataLight.to_numpy().tolist(),
                                                        dataRaw=dataLightRaw.to_numpy().tolist())
            print(self.results.sensorResult)
            self.results.interfaceResult = DataInterface(interfaceFound=interfaceFound,
                                                         interfacePosition=interfacePosition,
                                                         lastScanTime=datetime.now())
            self.results.drainResult = DataDrain()
            self.status = Status.finished

    def startScanAndFind(self, lType, settings):
        print("Starting scan and find")
        self.stopEvent.clear()
        self.settings = settings
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runScanAndFind(lType), backLoop)
        # print(asyncio.all_tasks(self._loop))

    async def runScanAndFind(self, lType):
        print("Running scan and Find")
        self.error = ""

        LLEProc.setLiquidType(lType)

        dataLight, dataLightRaw, _, error = LLEProc.scanFunnel(self.settings.scanSettings.initialLEDs,
                                                               self.settings.scanSettings.deltaLEDs,
                                                               self.settings.scanSettings.travelDistance,
                                                               self.stopEvent)
        # dataLight.loc[0,'A'] = 0.00
        # print(dataLight.info())
        if error != "":
            self.error = self.error + ", " + error
        interfaceFound, interfacePosition, error = LLEProc.findInterface(dataLight,
                                                                         self.settings.detectionSettings.smoothWindowSize,
                                                                         self.settings.detectionSettings.smoothProminence,
                                                                         self.settings.detectionSettings.gradient2Prominence)
        if error != "":
            self.error = self.error + ", " + error

        self.results.sensorResult = DataLightSensor(data=dataLight.to_numpy().tolist(),
                                                    dataRaw=dataLightRaw.to_numpy().tolist())
        self.results.interfaceResult = DataInterface(interfaceFound=interfaceFound, interfacePosition=interfacePosition,
                                                     lastScanTime=datetime.now())
        self.status = Status.finished

    def returnSensorData(self, idN: int):
        print("Returning sensor data with id: " + str(idN))
        df = LLEProc.getSensorData(idN)
        dfRaw = LLEProc.getSensorDataRaw(idN)
        return df, dfRaw

    def startDrainToPort(self, ml, port):
        print("Starting drain experiment")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runDrainMlToPort(ml, port), backLoop)

    async def runDrainMlToPort(self, ml, port):
        print("Running drain ml to port")
        portDrained, mlToDrain, conversionFactor, secondsToDrain, error = await LLEProc.drainMlToPort(ml, port)
        self.results.drainResult = DataDrain(mlToDrainLower=mlToDrain, conversionFactorLower=conversionFactor,
                                             secondsLower=secondsToDrain)
        self.status = Status.finished

    def startPumpFromPort(self, ml, port):
        print("Starting pump")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runPumpMlFromPort(ml, port), backLoop)

    async def runPumpMlFromPort(self, ml, port):
        print("Running pump ml from port")
        portPumped, mlToPump, conversionFactor, secondsToPump, error = await LLEProc.pumpMlFromPort(ml, port, 0)
        self.results.pumpResult = DataPump(mlToPump=mlToPump, conversionFactor=conversionFactor,
                                           secondsToPump=secondsToPump)
        logging.info("Pump finished")
        self.status = Status.finished

    def startDrainUpperToPort(self, port):
        print("Starting drain upper layer to port")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runDrainUpperToPort(port), backLoop)

    async def runDrainUpperToPort(self, port):
        print("Running drain upper layer to port")
        _, mlToDrainUpper, conversionFactorUpper, secondsToDrainUpper, error = await LLEProc.drainUpperPhase(port)
        if error != "":
            self.error = self.error + ", " + error
            print(error)
        self.results.drainResult = DataDrain(mlToDrainUpper=mlToDrainUpper, conversionFactorUpper=conversionFactorUpper,
                                             secondsUpper=secondsToDrainUpper)
        self.status = Status.finished

    def startDrainLowerToPort(self, port, interfacePosition, tubingSensor=True):
        print("Starting drain lower layer to port")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(
            self.runDrainLowerToPort(port, interfacePosition, tubingSensor), backLoop)
        self.runningTask.exception

    async def runDrainLowerToPort(self, port, interfacePosition, tubingSensor=True):
        print("Running drain lower layer to port")

        mlToDrainLower = 0.0
        conversionFactorLower = 0.0
        secondsToDrainLower = 0.0
        print(interfacePosition)

        if interfacePosition != None:
            # print(interfacePosition)
            _, mlToDrainLower, conversionFactorLower, secondsToDrainLower, error = await LLEProc.drainLowerPhase(port,
                                                                                                                 interfacePosition,
                                                                                                                 tubingSensor)
        elif self.results.interfaceResult != None:
            _, mlToDrainLower, conversionFactorLower, secondsToDrainLower, error = await LLEProc.drainLowerPhase(port,
                                                                                                                 self.results.interfaceResult.interfacePosition,
                                                                                                                 tubingSensor)
        else:
            error = "No interface position set to drain the lower layer"
            print(error)

        if error != "":
            self.error = self.error + ", " + error

        self.results.drainResult = DataDrain(mlToDrainLower=mlToDrainLower, conversionFactorLower=conversionFactorLower,
                                             secondsLower=secondsToDrainLower)
        print(self.results.drainResult)
        self.status = Status.finished

    def startMoveValveToPort(self, port):
        print("Starting move valve to port")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runMoveValveToPort(port), backLoop)

    async def runMoveValveToPort(self, port):
        print("Running move valve to port")
        error = ""
        valveCurrentPort = LLEProc.moveValveToPort(port)
        if valveCurrentPort == -1:
            error = "Valve could not reach port"
        if error != "":
            self.error = self.error + ", " + error
        self.status = Status.finished

    def startMovePump(self, speed, dir):
        print("Starting move pump")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(self.runMovePump(speed, dir), backLoop)

    async def runMovePump(self, speed, dir):
        print("Running move pump")
        print("Speed", speed)
        print("Dir", dir)
        error = ""
        success = LLEProc.startPump(speed, dir)
        if success != 1:
            error = "Could not move pump"
        if error != "":
            self.error = self.error + ", " + error
        print(success)
        self.status = Status.finished

    def startDrainToLowestDetectionPoint(self, port, interfacePosition):
        print("Starting drain lower layer to lowest detection point")
        self.stopEvent.clear()
        self.status = Status.running
        self.runningTask = asyncio.run_coroutine_threadsafe(
            self.runDrainToLowestDetectionPoint(port, interfacePosition), backLoop)
        self.runningTask.exception

    async def runDrainToLowestDetectionPoint(self, port, interfacePosition):
        print("Running drain lower layer to lowest detection point")

        mlToDrainLower = 0.0
        conversionFactorLower = 0.0
        secondsToDrainLower = 0.0
        print(interfacePosition)

        if interfacePosition != None:
            # print(interfacePosition)
            _, mlToDrainLower, conversionFactorLower, secondsToDrainLower, success, error = await LLEProc.drainToLowestDetectionPoint(
                port,
                interfacePosition)
        elif self.results.interfaceResult != None:
            _, mlToDrainLower, conversionFactorLower, secondsToDrainLower, success, error = await LLEProc.drainToLowestDetectionPoint(
                port,
                self.results.interfaceResult.interfacePosition)
        else:
            error = "No interface position set to drain the lower layer"
            print(error)

        if error != "":
            self.error = self.error + ", " + error

        if success:
            print("Drained to lowest detection point")
        else:
            print("Already at or beyond lowest detection point")

        self.status = Status.finished


# Create app
app = FastAPI()

extractor = LiquidExtractor()


@app.on_event("startup")
async def startup_event():
    t = Thread(target=start_background_loop, args=(backLoop,), daemon=True)
    t.start()


# Endpoints

# Get /
# Get the basic information from the server
@app.get("/")
async def rootPath():
    return {"name": "LLE",
            "Device id": 1}


@app.post("/startSettling", response_model=StatusResponse)
def post_Settling_start(settings: Settings = None, background_tasks: BackgroundTasks = None):
    print(settings)
    if settings == None:
        settings = Settings()
        print("Didnt receive settings")
    if background_tasks != None:
        background_tasks.add_task(extractor.startSettlingExp, settings)
    else:
        return {"Message": "Background tasks not started"}
    return StatusResponse(status=Status.running)


@app.post("/startDraining/{lType}", response_model=StatusResponse)
def post_start(lType: str, settings: Settings = None, background_tasks: BackgroundTasks = None):
    if settings == None:
        settings = Settings()
    if background_tasks != None:
        background_tasks.add_task(extractor.startDrainExp, lType, settings)
    else:
        return {"Message": "Background tasks not started"}
    return StatusResponse(status=Status.running)


@app.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(status=extractor.status)


@app.get("/stop", response_model=StatusResponse)
def do_stop():
    extractor.stop()
    return StatusResponse(status=extractor.status)


@app.get("/results", response_model=ResultsResponse)
def get_results():
    return ResultsResponse(status=extractor.status, results=extractor.results, error=extractor.error)


# LLE Scan and Find requests
@app.post("/startScanFind/{lType}", response_model=StatusResponse)
async def do_ScanFind_Run(lType: str, settings: Settings = None, background_tasks: BackgroundTasks = None):
    settings = Settings()
    background_tasks.add_task(extractor.startScanAndFind, lType, settings)
    return StatusResponse(status=Status.running)


@app.get("/drainToPort/{port}/{ml}", response_model=StatusResponse)
def get_drainToPort(port: int, ml: float, background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startDrainToPort, ml, port)
    return StatusResponse(status=Status.running)


# Get /imageData Procedures
@app.get("/pumpFromPort/{port}/{ml}", response_model=StatusResponse)
def get_pumpFromPort(port: int, ml: float, background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startPumpFromPort, ml, port)
    return StatusResponse(status=Status.running)


@app.get("/DrainLowerLayer/{port}", response_model=StatusResponse)  # /DrainLowerLayer/{port}?50.3
async def do_DrainLowerToPort(port: int, intPos: float = None, tubingSensor: bool = True,
                              background_tasks: BackgroundTasks = None):
    background_tasks.add_task(extractor.startDrainLowerToPort, port, intPos, tubingSensor)
    return StatusResponse(status=Status.running)


@app.get("/DrainUpperLayer/{port}", response_model=StatusResponse)
async def do_DrainUpperToPort(port: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startDrainUpperToPort, port)
    return StatusResponse(status=Status.running)


@app.get("/moveValve/{port}", response_model=StatusResponse)
async def do_MoveValveToPort(port: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startMoveValveToPort, port)
    return StatusResponse(status=Status.running)


@app.get("/movePump/{speed}/{dir}", response_model=StatusResponse)
async def do_MovePump(speed: int, dir: bool, background_tasks: BackgroundTasks):
    background_tasks.add_task(extractor.startMovePump, speed, dir)
    return StatusResponse(status=Status.running)


@app.get("/DrainLowerToLowestDetectionPoint/{port}", response_model=StatusResponse)  # /DrainLowerLayer/{port}?50.3
async def do_DrainLowerToLowestDetectionPoint(port: int, intPos: float = None,
                                              background_tasks: BackgroundTasks = None):
    background_tasks.add_task(extractor.startDrainToLowestDetectionPoint, port, intPos)
    return StatusResponse(status=Status.running)


# LLE Settling requests
# @app.get("/start/Settling",response_model=Response)
# async def do_Settling_Run(background_tasks: BackgroundTasks):
#     settings = Settings()
#     background_tasks.add_task(extractor.startSettlingExp,settings)
#     return Response(status=extractor.status, settings=extractor.settings)


@app.get("/sensorData/{item_id}", response_model=ResultsResponse)
def getSensorData(item_id: int):
    df, dfRaw = extractor.returnSensorData(item_id)
    return ResultsResponse(status=extractor.status, results=LLEOutputs(
        sensorResult=DataLightSensor(data=df.to_numpy().tolist(), dataRaw=dfRaw.to_numpy().tolist())))


@app.put("/setInterfacePosition/{intPos}")
def setInterfacePosition(intPos: float):
    extractor.results.interfaceResult = DataInterface(interfaceFound=False, interfacePosition=intPos)
    error = LLEProc.setInterfacePosition(intPos)
    extractor.error = extractor.error + ", " + error
    # return ResultsResponse(status=extractor.status,results=extractor.results,error=extractor.error)
    return {"success": True}


@app.get("/calculateVolume")
def calculateVolumeFromPosition(position: float = None, initialVolume: float = 300, tubingVolume: float = 0,
                                r: float = 0.0455, funnelAngle: float = 0.296706):
    if position == None:
        if extractor.results.interfaceResult == None:
            position = 0.0
            source = "Default"
        else:
            position = extractor.results.interfaceResult.interfacePosition
            source = "Last Scan"
    else:
        source = "Parameter"
    # print(position)
    sensorPosition = (position - 15) * 0.001
    # volume = LLEProc.calculateVolumeFulstrum(initialVolume,tubingVolume,r,sensorPosition,funnelAngle)
    volume = LLEProc.calculateVolumeRegression(position)
    return {"volume(ml)": volume, "source": source}


def zipfiles(filenames):
    zip_subdir = "Images"
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = BytesIO()
    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = os.path.join(zip_subdir, fname)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed")
    # ..and correct content-disposition
    # resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


# #Get /imageData Procedures
@app.get("/imageData")
def getImageData(id: int = None):
    if id == None:
        imageFolderPath = LLEProc.getLastImageDataFolderPath()
    else:
        imageFolderPath = LLEProc.getImageDataFolderPath(id)

    imageList = os.listdir(imageFolderPath)
    for i in range(len(imageList)):
        imageList[i] = imageFolderPath + "/" + imageList[i]

    parentPath = imageFolderPath[0:imageFolderPath.find("/")]

    imageList.append(parentPath + "/data.csv")
    imageList.append(parentPath + "/dataRAW.csv")

    # return {"imageFolderPath":imageFolderPath,"imageList":imageList,"parentPath":parentPath}
    return zipfiles(imageList)

    # return {"imageData": returnJson}


# Get the last image data obtained when scanning the interface


def main():
    uvicorn.run("software.API.FastAPI.BeltDrainLLE.BeltDrainLLE:app", host='0.0.0.0', port=8000)


if __name__ == "__main__":
    main()




