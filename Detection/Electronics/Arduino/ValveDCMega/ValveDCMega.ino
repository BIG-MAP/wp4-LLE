
//Solenoid valves
#define SOL0 35
#define SOL1 37
#define SOL2 39

//Refill pump
#define PWMA 3
#define DIRA 12
#define BRAKEA 9

//Drain pump
#define PWMB 11
#define DIRB 13
#define BRAKEB 8

char x;

bool S0 = false;
bool S1 = false;
bool S2 = false;

void setup() {
  // put your setup code here, to run once:
  pinMode(PWMA, OUTPUT);
  pinMode(DIRA, OUTPUT);
  pinMode(BRAKEA, OUTPUT);
  pinMode(PWMB, OUTPUT);
  pinMode(DIRB, OUTPUT);
  pinMode(BRAKEB, OUTPUT);

  pinMode(SOL0, OUTPUT);
  pinMode(SOL1, OUTPUT);
  pinMode(SOL2, OUTPUT);
  
  Serial.begin(115200);
  digitalWrite(BRAKEA, LOW);
  digitalWrite(BRAKEB, LOW);
  digitalWrite(DIRA, LOW);
  digitalWrite(DIRB, LOW);
  analogWrite(PWMB, 0);
  analogWrite(PWMA, 0);
  
}

void loop() {
  // put your main code here, to run repeatedly:

  while (!Serial.available());
  x = Serial.read();

  if(x=='m'){
     Serial.println("Mixer Pump");
     analogWrite(PWMA, 200);
     delay(10000);
     analogWrite(PWMA, 0);
     delay(1000);
  }

  if(x=='d'){
     Serial.println("Drain Pump");
     analogWrite(PWMB, 200);
     delay(10000);
     analogWrite(PWMB, 0);
     delay(1000);
  }

  if(x=='0'){
    Serial.println("Solenoid valve 0");
    if(S0==false){
      digitalWrite(SOL0,HIGH);
      S0 = true;
    }else{
      digitalWrite(SOL0,LOW);
      S0 = false;
    }
  }

  if(x=='1'){
    Serial.println("Solenoid valve 1");
    if(S1==false){
      digitalWrite(SOL1,HIGH);
      S1 = true;
    }else{
      digitalWrite(SOL1,LOW);
      S1 = false;
    }
  }

  if(x=='2'){
    Serial.println("Solenoid valve 2");
    if(S2==false){
      digitalWrite(SOL2,HIGH);
      S2 = true;
    }else{
      digitalWrite(SOL2,LOW);
      S2 = false;
    }
  }
  

}
