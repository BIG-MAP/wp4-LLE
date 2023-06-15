# Install missing packages
For the GUI to work the pysimplegui package must be installed on the Raspberry pi with the command

pip3 install pysimplegui

# Arduino code

For the GUI to work correctly the arduino code in the dataloggerA sketch in 'Electronics/Arduino/' in this same repository must be downloaded to the arduino board in the LLE device

# GUI

The different controls of the GUI are explained in the followinf sections:

## Sliders

The sliders are used to set the different parameters of the datalogging task before starting, by default the repetitions slider is frozen at a value of 1.
All sliders are disabled when any action is started (Button pressed) with the exception of the settling time and the measure interval which can be changed on the fly after starting to measure.

### Settling time (min)
Sets the settling time in minutes, it is only verified if the correponding checkbox is set, can be adjusted on the fly

### Measure interval when settling (s)
Sets the interval of measure while settling in seconds, can be adjusted on the fly

### Number of draining steps (ml)
Sets the number of steps for draining, each step drains approximately 1 ml and pauses for 3 seconds as the motors move

### Number of Repetitions
Cannot be adjusted for the current version of the experiments

## Image
The last image captured from the camera (not live) will be displayed on the upper right corner of the GUI

## Output
Displays the output of the different routines. However, all the measures taken will be saved in separate csv files with their name tagged by the current measure number(images are stored in their own folder which is named in a similar way) that is stored in the count.txt file.

## Buttons

The buttons are used to initiate or stop the device actions. All buttons will function properly when everything is correctly connected (Arduino + Sensor, USB Camera). If either the Arduino, the sensor or the USB camera are disconnected the buttons will malfunction.
All buttons will initiate by opening the serial port of the Arduino and waiting for 10 seconds, and will end in a similar way (closing and resetting the port and waiting for 10 seconds, this last wait cannot be canceled).

### Measure Start
Starts the measuring process given the parameters set on the sliders above, be sure that the funnel is filled from the bottle using the "Refill Funnel" button previous to using this button, the process works in the following sequence:
* The parameters from the window are read.
* The current experiment number is read from the count.txt file (Be sure to create the file in the same folder as the python script and save a value of zero in it if it does not exist). An example of the count.txt file can be found in this same folder.
* The camera focus will be adjusted (Only works in linux with the provided camera, be sure to adjust the cameraDev property at the beginning of the script accordingly).
* Files and folders are created
* The settling routine will start, taking measures according to the sliders corresponding values, at this time the "Drain" button will be active and can be pressed at any time to skip settling and start darining. If the "Use settling time" checkbox is unchecked the routine will run indefinitely until the "Drain" button is pressed.
* After the settling time is done, or the "Drain" button is pressed, the draining routine will start, at this time the "Pause Drain" button will be active and will pause the draining process if pressed, press it again to continue draining.
* When the draining routine is done and everything has finished correctly the output will read "Measure Finished" and the arduino will be reset.

### Drain
Only active while measuring, see the "Measure Start" button description.

### Pause Drain
Only active while measuring and draining, see the "Measure Start" button description.

### Refill Funnel
This button will start the pump that refills the funnel from the bottle, it will run for a total of 250 seconds.

### Empty Funnel
This button will start the pump that drains the funnel and moves the liquid to the bottle, it will run for a total of 250 seconds.

### Clean Hoses
This button will start both pumps at maximum speed for a total of 200 seconds. A cleaning solution can be put on the bottle to clean the hoses in conjunction with this action.

### Cancel
All routines can be canceled at any time by pressing this button, canceling will try to save and close all files and devices correctly before completely stopping, so a small delay may be noticeable before everything halts.
This button attempts to stop the Arduino by resetting the serial port connection so it will not work to halt the motors if the Arduino is disconnected. For these reasons be careful when using it as an emergency stop. 

### Exit
Exits the GUI
