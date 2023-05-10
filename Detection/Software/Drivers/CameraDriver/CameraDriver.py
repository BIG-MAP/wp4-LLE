import os
import cv2 as cv
import logging
from datetime import datetime

cap = None

if os.name == 'nt':
    cameraDev = 1
else:
    cameraDev = '/dev/video0'

def captureImage(path,name):
    global cap
    ret, frame = cap.read()
    if (ret):
        cv.imwrite(path+'/'+name,frame)
        metaDataFile = open(path+"/metadata.txt", "a")
        metaDataFile.write(name + ", "+str(datetime.now())+"\n")
        metaDataFile.close()
        return frame
    else:
        logging.info("Could not capture Image")
        exit()
    


def initCamera():
    global cap
    cap = cv.VideoCapture(cameraDev)

    if not cap.isOpened():
        print("Cannot open camera")
        return False

    cap.set(cv.CAP_PROP_BUFFERSIZE,1)
    print("Camera opened")
    return True

def closeCamera():
    global cap
    cap.grab()
    cap.release()

def focusCamera():
    global cap
    if(os.name != 'nt'): #Only works on linux with v4l and only for autofoc
        os.system("v4l2-ctl --device="+cameraDev+" -c focus_auto=0")
        os.system("v4l2-ctl --device="+cameraDev+" -c focus_absolute=60")
        os.system("v4l2-ctl --device="+cameraDev+" -c focus_absolute=160")
    cap.grab()