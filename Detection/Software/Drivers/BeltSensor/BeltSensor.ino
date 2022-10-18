#include <Arduino.h>
#include "DRV8825.h"
#include "SparkFun_AS7265X.h"
#include <Adafruit_DotStar.h>
#include <SPI.h> 

// Motor steps per revolution. Most steppers are 200 steps or 1.8 degrees/step
#define MOTOR_STEPS 200
#define RPM 60
// Microstepping mode. If you hardwired it to save pins, set to the same value here.
#define MICROSTEPS 16


#define DIR 3
#define STEP 2
#define ENABLE 4

DRV8825 stepper(MOTOR_STEPS, DIR, STEP, ENABLE);

#define TOP 6
#define HOME 5

AS7265X sensor;

#define NUMPIXELS 16 // Number of LEDs in strip

//(Arduino Uno = pin 11 for data, 13 for clock, other boards are different).
//Adafruit_DotStar strip(NUMPIXELS, DOTSTAR_BRG);

// Here's how to control the LEDs from any two pins:
#define DATAPIN    8
#define CLOCKPIN   9
Adafruit_DotStar strip(NUMPIXELS, DATAPIN, CLOCKPIN, DOTSTAR_BRG);

int      head  = 0, tail = 0; // Index of first 'on' and 'off' pixels
uint32_t color = 0xFF0000;      // 'On' color (starts red)

char command;
int cm = 50;
int mm = 5;


void setup() {
  // put your setup code here, to run once:
   Serial.begin(115200);
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

   
}

void loop() {
  // put your main code here, to run repeatedly:
  while(!Serial.available());
  command = Serial.read();

  if(command == 'h'){
     homeBelt();
     Serial.println("0");
  }

  if(command == 't'){
     topBelt();
     Serial.println("0");
  }

  if(command == 'u'){
     upCm();
     Serial.println("0");
  }

  if(command == 'd'){
     downCm();
     Serial.println("0");
  }

  if(command == 's'){
     upMm();
     Serial.println("0");
  }

  if(command == 'm'){
    measure();
  }

  if(command == 'o'){
    turnLEDsOff();
    Serial.println("0");
  }

  if(command == 'n'){
    turnLEDsOn();
    Serial.println("0");
  }

  if(command == 'a'){
    int recv = Serial.parseInt();
     
    if(recv>NUMPIXELS){
        head = NUMPIXELS;
    }else{
        if(recv<0){
            head = 0;
        }else{
            head = recv;
        }
    }

    if(head < tail){
      head = tail;
    }
    Serial.println("0");
  }

  if(command == 'l'){
    int recv = Serial.parseInt();
     
    if(recv>NUMPIXELS){
        tail = NUMPIXELS;
    }else{
        if(recv<0){
            tail = 0;
        }else{
            tail = recv;
        }
    }

    if(tail > head){
      tail = head;
    }
    Serial.println("0");
  }

  
}


void turnLEDsOff(){
   for(int i = tail;i<=head;i++){
    strip.setPixelColor(i,0);
    strip.show();
   }

   if((color >>= 8) == 0)      
      color = 0xFF0000;
}

void turnLEDsOn(){
  
   for(int i = tail;i<=head;i++){
    strip.setPixelColor(i,color);
    strip.show();
   }
   
   delay(20);
}

   



void upMm(){
  Serial.println("Moving up by 1 mm");
  
  int topRead = digitalRead(TOP);

  if(topRead == LOW){
    Serial.println("Already at the top");
  }else{

    stepper.enable();
  
    stepper.startMove(mm * MICROSTEPS);
  
    unsigned wait_time_micros = stepper.nextAction();
    topRead = digitalRead(TOP);
  
    while(wait_time_micros > 0 && topRead != LOW){
      wait_time_micros = stepper.nextAction();
      topRead = digitalRead(TOP);  
    }
    
    stepper.stop();
  
    stepper.disable();

  }
  
}

void upCm(){
  Serial.println("Moving up by 10 mm");
  
  int topRead = digitalRead(TOP);

  if(topRead == LOW){
    Serial.println("Already at the top");
  }else{

    stepper.enable();
  
    stepper.startMove(cm * MICROSTEPS);
  
    unsigned wait_time_micros = stepper.nextAction();
    topRead = digitalRead(TOP);
  
    while(wait_time_micros > 0 && topRead != LOW){
      wait_time_micros = stepper.nextAction();
      topRead = digitalRead(TOP);  
    }
    
    stepper.stop();
  
    stepper.disable();

  }
  
}

void downCm(){
  Serial.println("Moving down by 10 mm");

  int homeRead = digitalRead(HOME);

  if(homeRead == LOW){
    Serial.println("Already at home");
  }else{

    stepper.enable();
  
    stepper.startMove(-cm * MICROSTEPS);
  
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


void topBelt(){

  Serial.println("Topping");

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
  Serial.println("Count ");
  Serial.println(count);
  
  
}

void homeBelt(){
  Serial.println("Homing");

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

void measure(){

     sensor.takeMeasurements();
     //lastReading = analogRead(sensorPin);
     
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
     //Serial.print(",");
     //Serial.print(lastReading);
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
     //Serial.print(",");
     //Serial.print(lastReading);
     Serial.println();
}
