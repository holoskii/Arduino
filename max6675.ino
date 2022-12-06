// maivas@maivas-laptop:~$ 

// 0. Setup
// ls -la /dev/ttyACM0 && sudo chmod a+rw /dev/ttyACM0 && ls -la /dev/ttyACM0

// 1. Read
// cat -v /dev/ttyACM0 | tee ~/output.file

// 2. Process file:
// cat output.file | grep "Data" | awk  '{print $2}' | sed 's/..$//' > main.csv

// 3. Make a graph:
// python3 main.py

#include <LiquidCrystal_I2C.h>
#include <MAX6675_Thermocouple.h>
MAX6675_Thermocouple thermocouple(4, 5, 6); // SCK, CS, SO

unsigned long measureAtMsec = 0;
unsigned long updateInterval = 1000;


void setup() {
  Serial.begin(9600);
  Serial.println("\n\n\n\n\nSetup");
  pinMode(2, OUTPUT);    // sets the digital pin 13 as output
  pinMode(3, OUTPUT);    // sets the digital pin 13 as output
  digitalWrite(2, LOW);
  digitalWrite(3, HIGH);
  randomSeed(analogRead(0));
  delay(1000);
}

double celsius;
int c;
char buf[2550];

void loop() {
  // measureAtMsec = millis();
  // delay(updateInterval);
  if(measureAtMsec <= millis()) {
    measureAtMsec += updateInterval;
    // Serial.println("time,temp1Up,temp1Bottom,temp2Up,temp2Bottom");
    // Read a temperature in Celsius.
    celsius = thermocouple.readCelsius();
    c = (int)celsius;
    // Serial.println("temp, time:");
    snprintf(buf, 255, "Data %d,%lu", c, millis());
    Serial.println(buf);
  }
}



