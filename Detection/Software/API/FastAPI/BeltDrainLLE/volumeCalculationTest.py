import math



def calculateVolumeFulstrum(initialVolume,tubingVolume,r,deltaDistance,funnelAngle):
    """
        Returns the volume in ml given a distance from the reference initial volume point
        and its associated radius in the funnel
    """
    R = (deltaDistance*math.sin(funnelAngle)) + r
    h = deltaDistance*math.cos(funnelAngle) 
    radiusTerm = (R*R) + (R*r) + (r*r)
    v = (math.pi*h*radiusTerm)/3
    return v*1000000+initialVolume+tubingVolume


def getVolumeLowerPhase(interfacePosition: float) -> float:
    sensorBorderM = (interfacePosition - 15)*0.001

    volumeMl = calculateVolumeFulstrum(300,0,0.0455,sensorBorderM,0.296706)#80-5ml error Original 300 ml initial volume 10 ml tubing volume

    return volumeMl


interfacePosition = 5 

volume = getVolumeLowerPhase(interfacePosition)
print(volume)