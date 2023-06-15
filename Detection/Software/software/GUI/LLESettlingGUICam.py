import numpy as np
import cv2 as cv
import serial
import time
import os
import PySimpleGUI as sg

if os.name == 'nt':
    comPort = "COM3"
    cameraDev = 1
else:
    comPort = '/dev/ttyUSB0'
    cameraDev = '/dev/video0'

def waitWithCancel(waitTime):
    global cancel
    t = 0
    while t < (waitTime*2) and not cancel:
        time.sleep(0.5)
        t = t + 1

def resetArduinoSerial():
    time.sleep(0.5) #Wait for port to close
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    print("Resetting arduino serial port")
    time.sleep(10) #Hard wait as everything is stopped
    arduino.close()
    
def captureImage(path,subs1,subs2,cap,imgCounter,stage):
    ret, frame = cap.read()
    cv.imwrite(path+'/'+subs1+'a'+subs2+stage+str(imgCounter)+'.jpg',frame)
    frame = cv.resize(frame, (250, 250))
    imgbytes = cv.imencode('.png', frame)[1].tobytes() #Convert to png encoded bytes
    window['-image-'].update(data=imgbytes) #Update image canvas
   
def measure():
    global cancel
    global drain
    global pauseDrain
    global finishDrain
    
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    waitWithCancel(10)
    
    cap = cv.VideoCapture(cameraDev)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    cap.set(cv.CAP_PROP_BUFFERSIZE,1)
    print("Camera opened")
    
    #GUI parameters
    subs1 = "COMP1"
    subs2 = "COMP2"
    rep = int(values['-REP-'])
    useSettling = values['-USESETTLTIME-']
    settlingTime = int(values['-SETTL-'])*60
    intervalTime = int(values['-INTERV-'])
    nDrainSteps = int(values['-DRSTEPS-'])
    imgCounter = 0
    
    #Other process parameters TODO: get from GUI or file
    with open('count.txt', "r") as counterFile:
        start = int(counterFile.read())+1
    print("Start number ", start)
    
    
    
    # Folder path for images
    cwd = os.getcwd()
    imageFolderName = 'ImageData'
    
    for i in range(rep):
        if cancel:
            break
            
        #if not cancel: #Only for repeated measures
            #arduino.write(bytes('r', 'utf-8'))
            #print("Refilling")
            #waitWithCancel(251)
            #print("Done Refilling")
            
        
        if not cancel: 
            if(i%2 == 0) and os.name != 'nt': #Only works on linux with v4l
                os.system("v4l2-ctl --device=/dev/video0 -c focus_auto=0")
                os.system("v4l2-ctl --device=/dev/video0 -c focus_absolute=60")
                os.system("v4l2-ctl --device=/dev/video0 -c focus_absolute=160")
            cap.grab()
        
        imgCounter = 0

        imageFolderPath = cwd +'/'+ subs1 + 'a' + subs2 + imageFolderName + str(i+start)
        os.mkdir(imageFolderPath)        
            
        fileName=subs1+'a'+subs2+'spectro-data'+str(i+start)+'.csv' #name of the CSV file generated
        fileNameRaw=subs1+'a'+subs2+'spectro-data'+str(i+start)+'RAW.csv' #name of the CSV file generated
    
        file = open(fileName, "a")
        fileRaw = open(fileNameRaw, "a")
        print("Created files")
        line  = 0
        
        with open('count.txt', "w") as counterFile:
            counterFile.write(str(i+start))
    
        data = "A,B,C,D,E,F,G,H,I,J,K,L,R,S,T,U,V,W,Res,Stage,Interval"
        file.write(data + "\n") #write data with a newline
        fileRaw.write(data + "\n") #write data with a newline
        
        #Time variables
        startTime = time.time()
        intervalStart = startTime
        elapsed = 0
        elapsedInterval = 0
        
        window['-DRSTEPS-'].update(disabled=False)
        print("Settling...")
        
        #Measure while settling
        while not cancel and (not drain and (elapsed <= settlingTime or not useSettling)):
            current = time.time()
            elapsedInterval = current - intervalStart
            elapsed = current-startTime
            
            settlingTime = int(values['-SETTL-'])*60
            intervalTime = int(values['-INTERV-'])
        
            if elapsedInterval >= intervalTime:
                #Take measure
            
                arduino.write(bytes('m', 'utf-8'))
                #waitWithCancel(1)
                getData= arduino.readline()
                data = getData.decode('utf-8').rstrip()
            
                getData= arduino.readline()
                dataRaw = getData.decode('utf-8').rstrip()
                
                captureImage(imageFolderPath,subs1,subs2,cap,imgCounter,"Settling")
                imgCounter = imgCounter + 1
            
                line = line + 1
                print(str(line))
                data = data+',Settling, '+str(intervalTime)
                dataRaw = dataRaw+',Settling, '+str(intervalTime)
                
                print(data)
                print(dataRaw)
            
                #add the data to the files
                file.write(data + "\n") #write data with a newline
                fileRaw.write(dataRaw + "\n") #write data with a newline
            
                print('Measure taken after (s)',elapsedInterval)
                elapsedInterval = 0
                intervalStart = time.time()
                
        
        while not cancel and not finishDrain:
        
            window['-DRAINBTN-'].update(disabled=True)
            window['-PAUSEBTN-'].update(disabled=False)
            window['-FINISHBTN-'].update(disabled=True)
            window['-DRSTEPS-'].update(disabled=True)
            nDrainSteps = int(values['-DRSTEPS-'])            
             
            print("Draining ....")
            
            for j in range(nDrainSteps):
                if cancel:
                    break
                
                
                arduino.write(bytes('s', 'utf-8'))
                waitWithCancel(3)
            
                arduino.write(bytes('m', 'utf-8'))
                #time.sleep(1)
                getData= arduino.readline()
                data = getData.decode('utf-8').rstrip()
            
                getData= arduino.readline()
                dataRaw = getData.decode('utf-8').rstrip()
            
                captureImage(imageFolderPath,subs1,subs2,cap,imgCounter,"Draining")
                imgCounter = imgCounter + 1
            
                line = line + 1
                print(str(line))
            
                data = data+',Draining, 3'
                dataRaw = dataRaw+',Draining, 3'
                print(data)
                print(dataRaw)

                #add the data to the files
                file.write(data + "\n") #write data with a newline
                fileRaw.write(dataRaw + "\n") #write data with a newline
            
                while not cancel and pauseDrain:
                    print('Paused ...')
                    waitWithCancel(0.5)
            
            drain = False
            window['-DRAINBTN-'].update(disabled=False)
            window['-PAUSEBTN-'].update(disabled=True)
            window['-FINISHBTN-'].update(disabled=False)
            window['-DRSTEPS-'].update(disabled=False)
            
            
            while not cancel and (not finishDrain and (not drain)):
                print("Press drain again to drain a new amount, otherwise press Finish Draining")
                print(drain)
                waitWithCancel(1)
                
            
        print("Logged "+str(line)+" lines in "+str(i))
        file.close()
        fileRaw.close()
        cap.grab()        
    
        waitWithCancel(2)
            
    if not cancel:
        print("Measure Finished")
        finishDrain = False
    else:
        print("Measure interrupted")
        cancel = False
        pauseDrain = False
        drain = False
        finishDrain = False
        window['-PAUSEBTN-'].update('Pause Drain')
        window['-PAUSEBTN-'].update(disabled=True)

    arduino.close()
    cap.release()
    resetArduinoSerial()    


def refillFunnel():
    global cancel
    print("Press cancel to stop at any time")
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    waitWithCancel(10)
    if not cancel:
        arduino.write(bytes('r', 'utf-8'))
    waitWithCancel(251)
    if not cancel:
        print("Done Refilling")
    else:
        print("Refilling interrupted")
        cancel = False
    arduino.close()
    resetArduinoSerial()


def emptyFunnel():
    global cancel
    print("Press cancel to stop at any time")
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    waitWithCancel(10)
    if not cancel:
        arduino.write(bytes('e', 'utf-8'))
    waitWithCancel(251)
    if not cancel:
        print("Done emptying")
    else:
        print("Emptying interrrupted")
        cancel = False 
    arduino.close()
    resetArduinoSerial()

def cleanHoses():
    global cancel
    print("Press cancel to stop at any time")
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    waitWithCancel(10)
    if not cancel:
        arduino.write(bytes('c', 'utf-8'))
    waitWithCancel(201)
    if not cancel:
        print("Done cleaning")
    else:
        print("Cleaning interrrupted")
        cancel = False
    arduino.close()
    resetArduinoSerial()
    
    
def disableAllButtons():
    window['Measure Start'].update(disabled=True)
    window['Refill Funnel'].update(disabled=True)
    window['Empty Funnel'].update(disabled=True)
    window['-FINISHBTN-'].update(disabled=True)
    window['-SETTL-'].update(disabled=False)
    window['-INTERV-'].update(disabled=False)
    window['-DRSTEPS-'].update(disabled=True)
    window['-REP-'].update(disabled=True)
    window['-USESETTLTIME-'].update(disabled=True)

    
def enableAllButtons():
    window['Measure Start'].update(disabled=False)
    window['Refill Funnel'].update(disabled=False)
    window['Empty Funnel'].update(disabled=False)
    window['-FINISHBTN-'].update(disabled=True)
    window['-SETTL-'].update(disabled=False)
    window['-INTERV-'].update(disabled=False)
    window['-DRSTEPS-'].update(disabled=False)
    window['-REP-'].update(disabled=True)
    window['-USESETTLTIME-'].update(disabled=False)
    window['-DRAINBTN-'].update(disabled=True)
    window['-PAUSEBTN-'].update(disabled=True)
    

    
    
col = [[sg.Text('Settling time (min)'), sg.Slider(orientation ='horizontal', key='-SETTL-', range=(5,240),enable_events=True),sg.Checkbox('Use Settling time', default=True,key='-USESETTLTIME-')],
       [sg.Text('Measure interval when settling (s)'), sg.Slider(orientation ='horizontal', key='-INTERV-', range=(2,120),default_value=30,enable_events=True)],
       [sg.Text('Number of draining steps (ml)'), sg.Slider(orientation ='horizontal', key='-DRSTEPS-', range=(1,300),default_value=250)],
       [sg.Text('Number of Repetitions'), sg.Slider(orientation ='horizontal', key='-REP-', range=(1,15),disabled = True)],
       [sg.Button('Measure Start',size=(20,2), font='24'),sg.Button('Drain',size=(20,2), font='24',key='-DRAINBTN-',disabled = True)],
       [sg.Button('Refill Funnel',size=(20,2), font='24'),sg.Button('Pause Drain',size=(20,2), font='24',key='-PAUSEBTN-',disabled = True)],
       [sg.Button('Empty Funnel',size=(20,2), font='24'),sg.Button('Finish Draining',size=(20,2), font='24',key='-FINISHBTN-',disabled=True)]]    

    
layout = [[sg.Column(col),sg.VerticalSeparator(),sg.Image(filename='', key='-image-')],
          [sg.Output(size=(160, 10),key='-OUTPUTLINES-')],
          [sg.Cancel(size=(20,2), font='24'), sg.Exit(size=(20,2), font='24')]]
          
          
          
window = sg.Window('LLE Detection', layout)

finishDrain = False
drain = False
pauseDrain = False
cancel = False
init = True
while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    if event == '-FINISHBTN-':
        finishDrain = True
        #disableAllButtons()
        #window.perform_long_operation(cleanHoses, '-OPERATION DONE-')
    if event.startswith('Empty'):
        disableAllButtons()
        window.perform_long_operation(emptyFunnel, '-OPERATION DONE-')
    if event.startswith('Refill'):
        disableAllButtons()
        window.perform_long_operation(refillFunnel, '-OPERATION DONE-')
    if event.startswith('Measure'):
        disableAllButtons()
        window['-DRAINBTN-'].update(disabled=False)
        window.perform_long_operation(measure, '-OPERATION DONE-')
    if event =='Cancel' :
        cancel = True
    if event =='-DRAINBTN-' :
        drain = True
    if event =='-PAUSEBTN-' :
        if pauseDrain:
            pauseDrain = False
            window['-PAUSEBTN-'].update('Pause Drain')
        else:
            pauseDrain = True
            window['-PAUSEBTN-'].update('Continue Drain')
    if event == '-OPERATION DONE-':
        enableAllButtons()
    
    
    

window.close()
    
    
