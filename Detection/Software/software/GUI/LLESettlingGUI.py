import numpy as np
import serial
import time
import os
import PySimpleGUI as sg

if os.name == 'nt':
    comPort = "COM8"
else:
    comPort = '/dev/ttyUSB0'

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
   
def measure():
    global cancel
    
    arduino = serial.Serial(port=comPort, baudrate=115200, timeout=10)
    waitWithCancel(10)
    
    #GUI parameters
    subs1 = "COMP1"
    subs2 = "COMP2"
    rep = int(values['-REP-'])
    settlingTime = int(values['-SETTL-'])*60
    intervalTime = int(values['-INTERV-'])
    nDrainSteps = int(values['-DRSTEPS-'])
    
    #Other process parameters TODO: get from GUI or file
    start = 0
    
    for i in range(rep):
        if cancel:
            break
            
        if not cancel:
            arduino.write(bytes('r', 'utf-8'))
            print("Refilling")
            waitWithCancel(251)
            print("Done Refilling")
            
        
            
        fileName=subs1+'a'+subs2+'spectro-data'+str(i+start)+'.csv' #name of the CSV file generated
        fileNameRaw=subs1+'a'+subs2+'spectro-data'+str(i+start)+'RAW.csv' #name of the CSV file generated
    
        file = open(fileName, "a")
        fileRaw = open(fileNameRaw, "a")
        print("Created files")
        line  = 0
    
        data = "A,B,C,D,E,F,G,H,I,J,K,L,R,S,T,U,V,W,Stage"
        file.write(data + "\n") #write data with a newline
        fileRaw.write(data + "\n") #write data with a newline
        
        #Time variables
        startTime = time.time()
        intervalStart = startTime
        elapsed = 0
        elapsedInterval = 0
        
        print("Settling...")
        
        #Measure while settling
        while not cancel and elapsed <= settlingTime:
            current = time.time()
            elapsedInterval = current - intervalStart
            elapsed = current-startTime
        
            if elapsedInterval >= intervalTime:
                #Take measure
            
                arduino.write(bytes('m', 'utf-8'))
                #waitWithCancel(1)
                getData= arduino.readline()
                data = getData.decode('utf-8').rstrip()
            
                getData= arduino.readline()
                dataRaw = getData.decode('utf-8').rstrip()
            
                line = line + 1
                print(str(line))
                data = data+',Settling'
                dataRaw = dataRaw+',Settling'
                
                print(data)
                print(dataRaw)
            
                #add the data to the files
                file.write(data + "\n") #write data with a newline
                fileRaw.write(dataRaw + "\n") #write data with a newline
            
                print('Measure taken after (s)',elapsedInterval)
                elapsedInterval = 0
                intervalStart = time.time()
                
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
            
            line = line + 1
            print(str(line))
            
            data = data+',Draining'
            dataRaw = dataRaw+',Draining'
            print(data)
            print(dataRaw)

            #add the data to the files
            file.write(data + "\n") #write data with a newline
            fileRaw.write(dataRaw + "\n") #write data with a newline
            
        print("Logged "+str(line)+" lines in "+str(i))
        file.close()
        fileRaw.close() 
    
        waitWithCancel(2)
            
    if not cancel:
        print("Measure Finished")
    else:
        print("Measure interrupted")
        cancel = False

    arduino.close()
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
    window['Measure'].update(disabled=True)
    window['Refill Funnel'].update(disabled=True)
    window['Empty Funnel'].update(disabled=True)
    window['Clean hoses'].update(disabled=True)
    window['-SETTL-'].update(disabled=True)
    window['-INTERV-'].update(disabled=True)
    window['-DRSTEPS-'].update(disabled=True)
    window['-REP-'].update(disabled=True)
    
def enableAllButtons():
    window['Measure'].update(disabled=False)
    window['Refill Funnel'].update(disabled=False)
    window['Empty Funnel'].update(disabled=False)
    window['Clean hoses'].update(disabled=False)
    window['-SETTL-'].update(disabled=False)
    window['-INTERV-'].update(disabled=False)
    window['-DRSTEPS-'].update(disabled=False)
    window['-REP-'].update(disabled=False)
    
    
col = [[sg.Text('Settling time (min)'), sg.Slider(orientation ='horizontal', key='-SETTL-', range=(5,120))],
       [sg.Text('Mesure interval when settling (s)'), sg.Slider(orientation ='horizontal', key='-INTERV-', range=(1,30),default_value=10)],
       [sg.Text('Number of draining steps (ml)'), sg.Slider(orientation ='horizontal', key='-DRSTEPS-', range=(245,255),default_value=250)],
       [sg.Text('Number of Repetitions'), sg.Slider(orientation ='horizontal', key='-REP-', range=(1,15))],
       [sg.Button('Measure',size=(20,2), font='24'),sg.Button('Refill Funnel',size=(20,2), font='24')],
       [sg.Button('Empty Funnel',size=(20,2), font='24'),sg.Button('Clean hoses',size=(20,2), font='24')]]    

    
layout = [[sg.Column(col)],
          [sg.Output(size=(80, 10),key='-OUTPUTLINES-')],
          [sg.Cancel(size=(20,2), font='24'), sg.Exit(size=(20,2), font='24')]]
          
          
          
window = sg.Window('Window that stays open', layout)

cancel = False
while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    if event.startswith('Clean'):
        disableAllButtons()
        window.perform_long_operation(cleanHoses, '-OPERATION DONE-')
    if event.startswith('Empty'):
        disableAllButtons()
        window.perform_long_operation(emptyFunnel, '-OPERATION DONE-')
    if event.startswith('Refill'):
        disableAllButtons()
        window.perform_long_operation(refillFunnel, '-OPERATION DONE-')
    if event.startswith('Measure'):
        disableAllButtons()
        window.perform_long_operation(measure, '-OPERATION DONE-')
    if event =='Cancel' :
        cancel = True
    if event == '-OPERATION DONE-':
        enableAllButtons()
    
    
    

window.close()
    
    
