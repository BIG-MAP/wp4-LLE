#include <Arduino.h>
#include "DRV8825.h"
#include "SparkFun_AS7265X.h"
#include <Adafruit_DotStar.h>
#include <SPI.h> 
#include <CmdMessenger.h>  // CmdMessenger

CmdMessenger cmdMessenger(Serial,',',';','/');

// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200
#define RPM 60
// Microstepping mode. If you hardwired it to save pins, set to the same value here.
#define MICROSTEPS 16

#define DIR 4 //4
#define STEP 3 //3
#define ENABLE 2 //2

DRV8825 stepper(MOTOR_STEPS, DIR, STEP, ENABLE);

#define TOP 6
#define HOME 5

AS7265X sensor;

#define NUMPIXELS 16 // Number of LEDs in strip

// Here's how to control the LEDs from any two pins:
#define DATAPIN    10
#define CLOCKPIN   9
Adafruit_DotStar strip(NUMPIXELS, DATAPIN, CLOCKPIN, DOTSTAR_BRG);

int      head  = -1; // Index of first 'on' and 'off' pixels
uint32_t color = 0xFF0000;      // 'On' color (starts red)

char command;
const int cm = 800;
const int mm = 80;
const int mmH = 84;

// This is the list of recognized commands. These can be commands that can either be sent or received. 
// In order to receive, attach a callback function to these events
enum
{
  // Commands
  kWatchdog            , // Command to request application ID
  kAcknowledge         , // Command to acknowledge a received command
  kError               , // Command to message that an error has occurred
  kHomeBelt        , // Command to Home the belt at the bottom of the funnel             
  kTopBelt        , // Command to move the belt to the top of the funnel               
  kUpCm       , // Command to move the belt up by 1 cm  
  kDownCm  , // Command to move the belt down by 1 cm   
  kUpMm  , // Command to move the belt up by 1 mm
  kLEDsOff  , // Command to turn off all LEDs on the strip
  kLEDsOn  , // Command to turn on the selected number of LEDs
  kSetNumberOfLEDs  , // Command to set the number of LEDs to turn on (starts from 0)
  kGetSensorReading  ,  // Command to trigger a sensor reading an get the result
  kGetSensorReadingResult , // Command to respond to the get sensor reading command
  kGetSensorReadingResultRaw  ,  //  Command to respond to the get sensor reading command with raw readings
  kSetLEDBrightness ,  //  Command to respond to the get sensor reading command with raw readings
  kUpSteps ,  //  Command to move the sensor up by a specified number of steps
  
};

// Commands we send from the PC and want to receive on the Arduino.
// We must define a callback function in our Arduino program for each entry in the list below.
void attachCommandCallbacks()
{
  // Attach callback methods
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kWatchdog, OnWatchdogRequest);
  cmdMessenger.attach(kHomeBelt, OnHomeBelt);
  cmdMessenger.attach(kTopBelt, OnTopBelt);
  cmdMessenger.attach(kUpCm, OnUpCm);
  cmdMessenger.attach(kDownCm, OnDownCm);
  cmdMessenger.attach(kUpMm, OnUpMm);
  cmdMessenger.attach(kLEDsOff, OnLEDsOff);
  cmdMessenger.attach(kLEDsOn, OnLEDsOn);
  cmdMessenger.attach(kSetNumberOfLEDs, OnSetNumberOfLEDs);
  cmdMessenger.attach(kGetSensorReading, OnGetSensorReading);
  cmdMessenger.attach(kSetLEDBrightness, OnSetLEDBrightness);
  cmdMessenger.attach(kUpSteps, OnUpSteps);
}

// ------------------  C A L L B A C K S -----------------------

// Called when a received command has no attached function
void OnUnknownCommand()
{
  cmdMessenger.sendCmd(kError,"Command without attached callback");
}

void OnWatchdogRequest()
{
  // Will respond with same command ID and Unique device identifier.
  cmdMessenger.sendCmd(kWatchdog, "0000000-0000-0000-0000-00000000001");
}

// Callback function that responds that Arduino is ready (has booted up)
void OnArduinoReady()
{
  cmdMessenger.sendCmd(kAcknowledge,"Arduino ready");
}

void OnGetSensorReading()
{
  // 
  measure();  
}

void OnHomeBelt(){

  homeBelt();

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Homed belt");
  
}

void OnTopBelt(){

  topBelt();

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Belt moved to the top");
  
}

void OnUpCm(){

  upCm();
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Moved belt up 1 cm");
  
}

void OnDownCm(){

  downCm();
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Moved belt down 1 cm");
  
}


void OnUpMm(){
  
  upMm();
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Moved belt up 1 mm");
  
}

void OnLEDsOff(){

  turnLEDsOff();
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Turned LEDs off");
  
}

void OnLEDsOn(){

  turnLEDsOn();
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,"Turned LEDs on");
  
}

void OnSetNumberOfLEDs(){

  //Set the number of LEDs to turn on (Starts on 0)
  int recv = cmdMessenger.readBinArg<int>();

  head = -1;
  
  if (cmdMessenger.isArgOk()) {
       if(recv>15){
        head = 15;
      }else{
        if(recv<0){
          head = 0;
        }else{
          head = recv;
        }
      }
  }

  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,head);
}

void OnSetLEDBrightness(){
  //Set the brightness for a specific LED (starts on 0), brightness between 0 and 255
  //int led = cmdMessenger.readInt16Arg();
  int led = cmdMessenger.readBinArg<int>();
  if (cmdMessenger.isArgOk()) {
       if(led>15){
        led = 15;
      }else{
        if(led<0){
          led = 0;
        }
      }
  }

  //int brightness = cmdMessenger.readInt16Arg();
  int brightness = cmdMessenger.readBinArg<int>();

  if (cmdMessenger.isArgOk()) {
       if(brightness>255){
        brightness = 255;
      }else{
        if(brightness<0){
          brightness = 0;
        }
      }
  }

  setLEDBrightness(led,brightness);
  
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,brightness);
  
}

void OnUpSteps(){
  //Move the sensor up by a prespecified number of steps
  int recv = cmdMessenger.readBinArg<int>();

  upSteps(recv);
  
  // Send acknowledgment back to PC
  cmdMessenger.sendCmd(kAcknowledge,recv);
  
}

// ------------------ M A I N  ----------------------

void setup() {
  Serial.begin(115200);

  // Do not print newLine at end of command, 
  // in order to reduce data being sent
  cmdMessenger.printLfCr(false);

  pinMode(HOME, INPUT_PULLUP);
  pinMode(TOP, INPUT_PULLUP);

  stepper.begin(RPM, MICROSTEPS);
  stepper.setEnableActiveState(LOW);

  strip.begin(); // Initialize pins for output
  strip.show();  // Turn all LEDs off ASAP

  //Serial.println("Checking sensor");
  if(sensor.begin() == false)
  {
    Serial.println("Sensor does not appear to be connected. Please check wiring. Freezing...");
    while(1);
  }
  sensor.disableIndicator(); //Turn off the blue status LED 

  // Attach my application's user-defined callback methods
  attachCommandCallbacks();

  cmdMessenger.sendCmd(kAcknowledge,"Arduino has started!");

}

void loop() {
  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();

}

void homeBelt(){
  //Serial.println("Homing");
  stepper.enable();

  int homeRead = digitalRead(HOME);

  if(homeRead == LOW){
    stepper.move(-20 * MOTOR_STEPS * MICROSTEPS);
    stepper.stop();
  }

  homeRead = digitalRead(HOME);  
  
  stepper.startMove(100 * MOTOR_STEPS * MICROSTEPS);
  
  unsigned wait_time_micros = stepper.nextAction();
  
  while(homeRead != LOW){

    wait_time_micros = stepper.nextAction();
    
    if (wait_time_micros <= 0) {
       stepper.startMove(100 * MOTOR_STEPS * MICROSTEPS);
    }

    homeRead = digitalRead(HOME);
    
  }

  stepper.stop();
  stepper.disable();
}


void topBelt(){

  //Serial.println("Topping");

  long count = 0;

  stepper.enable();

  int topRead = digitalRead(TOP);

  if(topRead == LOW){
    stepper.move(20 * MOTOR_STEPS * MICROSTEPS);
    stepper.stop();
  }

  topRead = digitalRead(TOP);  
  
  stepper.startMove(-100 * MOTOR_STEPS * MICROSTEPS);
  
  unsigned wait_time_micros = stepper.nextAction();
  count = count + 1;
  
  while(topRead != LOW){

    wait_time_micros = stepper.nextAction();
    count = count + 1;
    
    if (wait_time_micros <= 0) {
       stepper.startMove(-100 * MOTOR_STEPS * MICROSTEPS);
    }

    topRead = digitalRead(TOP); 
    
  }

  stepper.stop();
  stepper.disable();
  //Serial.println("Count ");
  //Serial.println(count);
  
  
}

void upCm(){
    upSteps(cm);
}

void downCm(){
  //Serial.println("Moving down by 10 mm");

  int homeRead = digitalRead(HOME);

  if(homeRead == LOW){
    //Serial.println("Already at home");
  }else{

    stepper.enable();
  
    stepper.startMove(-cm);
  
    unsigned wait_time_micros = stepper.nextAction();
    homeRead = digitalRead(HOME);
  
    while(wait_time_micros > 0 && homeRead != LOW){
      wait_time_micros = stepper.nextAction();
      homeRead = digitalRead(HOME);  
    }
    
    stepper.stop();
  
    stepper.disable();

  }
  
}

void upSteps(int steps){

  //Serial.println("Moving up by 1 mm");
  
  int topRead = digitalRead(TOP);
  int homeRead = digitalRead(HOME);

  if(topRead == LOW || homeRead == LOW){
    //Serial.println("Already at the top");
  }else{

    stepper.enable();
  
    stepper.startMove(steps);
  
    unsigned wait_time_micros = stepper.nextAction();
    topRead = digitalRead(TOP);
    homeRead = digitalRead(HOME);
  
    while(wait_time_micros > 0 && (topRead != LOW && homeRead != LOW)){
      wait_time_micros = stepper.nextAction();
      topRead = digitalRead(TOP);
      homeRead = digitalRead(HOME);  
    }
    
    stepper.stop();
  
    stepper.disable();

  }
  
}

void upMm(){

  upSteps(mm);
  
}

void turnLEDsOff(){
   for(int i = 0;i<=head;i++){
    strip.setPixelColor(i,0);
    strip.show();
   }

   if((color >>= 8) == 0)      
      color = 0xFF0000;
}

void turnLEDsOn(){
  
   for(int i = 0;i<=head;i++){
    strip.setPixelColor(i,color);
    strip.show();
   }
   
   delay(20);
}

void setLEDBrightness(int led, int brightness){

  color = (uint32_t)brightness << 16;
  //Serial.print("Color");
  //Serial.println(color, HEX);
  //Serial.print("Brightness ");
  //Serial.println(brightness, DEC);

  strip.setPixelColor(led,color);
  strip.show();
  delay(20);
  
}


void measure(){

     sensor.takeMeasurements();

     cmdMessenger.sendCmdStart(kGetSensorReadingResult);
    
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedA());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedB());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedC());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedD());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedE());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedF());

     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedG());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedH());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedI());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedJ());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedK());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedL());

     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedR());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedS());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedT());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedU());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedV());
     cmdMessenger.sendCmdBinArg<float>(sensor.getCalibratedW());
     cmdMessenger.sendCmdEnd();

     cmdMessenger.sendCmdStart(kGetSensorReadingResultRaw);

     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getA());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getB());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getC());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getD());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getE());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getF());

     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getG());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getH());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getI());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getJ());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getK());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getL());

     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getR());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getS());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getT());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getU());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getV());
     cmdMessenger.sendCmdBinArg<uint16_t>(sensor.getW());
     cmdMessenger.sendCmdEnd();
}
