import time
import pandas as pd
import asyncio

from software.API.FastAPI.BeltDrainLLE import LLEBeltDrainProcedures as LLEProc

def drainOut(port:int,volume:int):
    asyncio.run(LLEProc.drainMlToPortSpeed(volume, port, 255))


def main():
    drainOut(2,2000)


if __name__ == "__main__":
    main()
