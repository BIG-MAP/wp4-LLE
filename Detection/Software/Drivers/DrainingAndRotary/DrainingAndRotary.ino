#include <Arduino.h>
#include "DRV8825.h"
#include "SparkFun_AS7265X.h"


// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200
#define RPM 120
#define RPMVALVE 60
// Microstepping mode. If you hardwired it to save pins, set to the same value here.
#define MICROSTEPS 16

#define DIRPUMP 10
#define STEPPUMP 9
#define ENAPUMP 8

#define DIRVALVE 4
#define STEPVALVE 3
#define ENAVALVE 2

#define HOME 5
#define PORT 6

DRV8825 stepperPump(MOTOR_STEPS, DIRPUMP, STEPPUMP, ENAPUMP);
DRV8825 stepperValve(MOTOR_STEPS, DIRVALVE, STEPVALVE, ENAVALVE);

AS7265X sensor;

char command;
boolean DEBUG = false;

//Draining Pump parameters
float mlPerDrain = 1;
float ml2DegreesMultiplier = 10;
bool rotationDir = true;

//Rotary valve parameters
bool homePort = false;
bool port = false;
int portNumber = 1;


void setup() {
  Serial.begin(115200);
  
  pinMode(HOME, INPUT_PULLUP);
  pinMode(PORT, INPUT_PULLUP);

  stepperPump.begin(RPM, MICROSTEPS);
  stepperPump.setEnableActiveState(LOW);

  stepperValve.begin(RPMVALVE,MICROSTEPS);
  stepperValve.setEnableActiveState(LOW);

  //Serial.println("Checking sensor");
  if(sensor.begin() == false)
  {
    Serial.println("Sensor does not appear to be connected. Please check wiring.");
  }
  sensor.disableIndicator(); //Turn off the blue status LED

  if(DEBUG){
    Serial.println("START");
  }
}

void loop() {
  //Wait for command
  while(!Serial.available());
  command = Serial.read();

  if(command != 'l' || command != 'r' || command != 's' || command != 'm' || command != 'i' || command != 'n' || command != 'h' || command != 'c' || command != 'd' || command != 't'){
    Serial.println("Unknown command");
  }

  if(command == 'l'){
    measure();
    Serial.println("0");
  }

  if(command == 'r'){
     drainMl(mlPerDrain,rotationDir);
     Serial.println("0");
  }

  if(command == 's'){
      float recv = Serial.parseFloat();
      if(recv>140){
        mlPerDrain = 140;
      }else{
        if(recv<0){
          mlPerDrain = 0;
        }else{
          mlPerDrain = recv;
        }
      }
      if(DEBUG){
        String preamble = "Setting drain to ";
        Serial.println(preamble + mlPerDrain);
      }
      
      Serial.println("0");
  }

  if(command=='m'){
      float recv = Serial.parseFloat();
      if(recv>500){
        ml2DegreesMultiplier = 500;
      }else{
        if(recv<0){
          ml2DegreesMultiplier = 0;
        }else{
          ml2DegreesMultiplier = recv;
        }
      }
      if(DEBUG){
        String preamble = "Setting multiplier to ";
        Serial.println(preamble + ml2DegreesMultiplier);
      }
      
      Serial.println("0");
   }

   if(command=='i'){
     if(rotationDir){
       rotationDir = false;
       if(DEBUG){
         Serial.println("Rotation set to false");
       }
     }else{
       rotationDir = true;
       if(DEBUG){
         Serial.println("Rotation set to true");
       }   
     } 
     Serial.println("0");  
   } 

  if(command == 'n'){
     moveToNexPort(true);
     returnPortNumber();
  }

  if(command == 'h'){
     moveToHomePort();
     returnPortNumber();
  }

  if(command == 'c'){
     returnPortNumber();
  }

  if(command == 'd'){
     if(DEBUG){
       DEBUG = false;
       Serial.println("Debug mode off");
     }else{
       DEBUG = true;
       Serial.println("Debug mode on");
     }
     Serial.println("0");
  }

  if(DEBUG){
    if(command == 't'){
       drainMl(20,rotationDir);
       moveValve45(true);
       Serial.println(digitalRead(HOME));
       Serial.println(digitalRead(PORT));
       Serial.println("0");
    }
  }
  
  
}


void drainMl(float ml,bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }

  float d = convertMltoDegrees(ml);

  if(DEBUG){
    String preamble = "Starting pump motor to move to ";
    Serial.println(preamble + d);
  }

  stepperPump.enable();

  stepperPump.rotate(dirMultiplier*d);

  stepperPump.stop();

  if(DEBUG){
    Serial.println("Holding half a second");
  }
  delay(500);

  stepperPump.disable();

  if(DEBUG){
    Serial.println("Pump motor stopped");
  }
}

float convertMltoDegrees(float ml){
    float d = ml*ml2DegreesMultiplier;
    return d;  
}

void moveToNexPort(bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }
  
  if(DEBUG){
    Serial.println("Starting Valve Motor");
  }
  
  stepperValve.enable();

  stepperValve.rotate(dirMultiplier*45);

  stepperValve.startRotate(dirMultiplier*50);

  while(digitalRead(PORT) != LOW){
     unsigned wait_time_micros = stepperValve.nextAction();
  }

  
  stepperValve.stop();

  if(DEBUG){
    Serial.println("Reached port, moving microsteps");
  }

  stepperValve.move(dirMultiplier*24);

  stepperValve.stop();

  stepperValve.disable();

  portNumber = portNumber + dirMultiplier;

  if(portNumber > 4){
    portNumber = 1;
  }

  if(portNumber < 1){
    portNumber = 4;
  }

  if(DEBUG){
    Serial.println("Reached port number");
    Serial.println(portNumber);
  }
  
}

void returnPortNumber(){
  Serial.println(portNumber);
 }

void moveToHomePort(){

    while(digitalRead(HOME) != LOW){
      moveToNexPort(true);
      delay(5000);
    }
  if(DEBUG){
    Serial.println("Reached Home!");
  }
    portNumber = 1;
}

void moveValve45(bool dir){
  int dirMultiplier = 1;
  if(!dir){
    dirMultiplier = -1;
  }

  Serial.println("Starting valve motor");
  stepperValve.enable();

  stepperValve.rotate(dirMultiplier*45);

  
  stepperValve.stop();

  stepperValve.disable();
}

void measure(){

     sensor.takeMeasurements();
     
     Serial.print(sensor.getCalibratedA());
     Serial.print(",");
     Serial.print(sensor.getCalibratedB());
     Serial.print(",");
     Serial.print(sensor.getCalibratedC());
     Serial.print(",");
     Serial.print(sensor.getCalibratedD());
     Serial.print(",");
     Serial.print(sensor.getCalibratedE());
     Serial.print(",");
     Serial.print(sensor.getCalibratedF());
     Serial.print(",");

     Serial.print(sensor.getCalibratedG());
     Serial.print(",");
     Serial.print(sensor.getCalibratedH());
     Serial.print(",");
     Serial.print(sensor.getCalibratedI());
     Serial.print(",");
     Serial.print(sensor.getCalibratedJ());
     Serial.print(",");
     Serial.print(sensor.getCalibratedK());
     Serial.print(",");
     Serial.print(sensor.getCalibratedL());
     Serial.print(",");

     Serial.print(sensor.getCalibratedR());
     Serial.print(",");
     Serial.print(sensor.getCalibratedS());
     Serial.print(",");
     Serial.print(sensor.getCalibratedT());
     Serial.print(",");
     Serial.print(sensor.getCalibratedU());
     Serial.print(",");
     Serial.print(sensor.getCalibratedV());
     Serial.print(",");
     Serial.print(sensor.getCalibratedW());
     Serial.println();

     Serial.print(sensor.getA());
     Serial.print(",");
     Serial.print(sensor.getB());
     Serial.print(",");
     Serial.print(sensor.getC());
     Serial.print(",");
     Serial.print(sensor.getD());
     Serial.print(",");
     Serial.print(sensor.getE());
     Serial.print(",");
     Serial.print(sensor.getF());
     Serial.print(",");

     Serial.print(sensor.getG());
     Serial.print(",");
     Serial.print(sensor.getH());
     Serial.print(",");
     Serial.print(sensor.getI());
     Serial.print(",");
     Serial.print(sensor.getJ());
     Serial.print(",");
     Serial.print(sensor.getK());
     Serial.print(",");
     Serial.print(sensor.getL());
     Serial.print(",");

     Serial.print(sensor.getR());
     Serial.print(",");
     Serial.print(sensor.getS());
     Serial.print(",");
     Serial.print(sensor.getT());
     Serial.print(",");
     Serial.print(sensor.getU());
     Serial.print(",");
     Serial.print(sensor.getV());
     Serial.print(",");
     Serial.print(sensor.getW());
     Serial.println();
}
