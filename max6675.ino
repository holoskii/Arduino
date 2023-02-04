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
// 2 - GND, 3 - 5V
MAX6675_Thermocouple thermocouple1(4, 5, 6); // SCK, CS, SO

unsigned long measureAtMsec = 0;
unsigned long updateInterval = 1000;


void setup() {
  Serial.begin(9600);
  Serial.println("\n\n\n\n\nSetup");
  
  // setup thermocouple1
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  digitalWrite(2, LOW);
  digitalWrite(3, HIGH);
  
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
    celsius = thermocouple1.readCelsius();
    c = (int)celsius;
    snprintf(buf, 255, "D %d,%lu", c, millis() / 1000);
    Serial.println(buf);
  }
}



