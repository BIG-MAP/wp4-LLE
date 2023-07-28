import time
import pandas as pd
import asyncio

from software.API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc

def fillIn(port:int,volume:int):
    asyncio.run(LLEProc.pumpMlFromPort(volume, port , 0))


def main():
    fillIn(1,2000)


if __name__ == "__main__":
    main()
