#include <LiquidCrystal_I2C.h>
// #include <max6675.h>



// -----------------------------------------------------------------------------------------
// MAX6675 thermocouple(10, 9, 8); // SCK, CS, SO
LiquidCrystal_I2C lcd(0x27, 20, 4);

uint32_t measureAtMsec = 0;
constexpr uint32_t updateInterval = 1000;

struct Reading {
  float voltage1, voltage2;
  float temp1Top, temp1Bottom;
  float temp2Top, temp2Bottom;
  uint64_t msecFromStart;
};

void scanReading(Reading& reading);
void printReading(const Reading& reading);

// -----------------------------------------------------------------------------------------

void setup() {
  lcd.init();
  lcd.backlight();
  // lcd.setCursor(0, 0);
  // lcd.print("Hello world");

  Serial.begin(9600);
  randomSeed(analogRead(0));
}


void loop() {
  if(measureAtMsec <= millis()) {
    measureAtMsec += updateInterval;
    Reading r;
    scanReading(r);
    printReading(r);
  }
}

// -----------------------------------------------------------------------------------------

void scanReading(Reading& reading) {
  reading.msecFromStart = millis();
  reading.temp1Top = random(300);
  reading.temp1Bottom = random(300);
  // reading.temp1Top = thermocouple.readCelsius();
  // reading.temp1Bottom = thermocouple.readCelsius() + random(300);
}

// -----------------------------------------------------------------------------------------
// Display interaction (buffers and printing)
constexpr size_t lineBufSize = 17;
constexpr size_t displayBufSize = 64;
char lineBuf[lineBufSize];
char displayBuf[displayBufSize] = {""};

void printReading(const Reading& reading) {
  int i0 = reading.msecFromStart / 1000UL;
  int i1 = random(300);
  int i2 = random(301);
  int i3 = random(302);
  int i4 = random(303);

  lcd.clear();
  lcd.setCursor(0, 0);
  snprintf(lineBuf, lineBufSize, "%d", i1);
  lcd.print(lineBuf);

  lcd.setCursor(0, 1);
  snprintf(lineBuf, lineBufSize, "%d", i2);
  lcd.print(lineBuf);

  lcd.setCursor(0, 2);
  snprintf(lineBuf, lineBufSize, "%d", i3);
  lcd.print(lineBuf);

  lcd.setCursor(0, 3);
  snprintf(lineBuf, lineBufSize, "%d", i4);
  lcd.print(lineBuf);

  snprintf(displayBuf, 64, "%d,%d,%d,", i0, i1, i2);
  Serial.print(displayBuf);
  lcd.setCursor(9, 0);
  lcd.print(displayBuf);

  snprintf(displayBuf, 64, "%d,%d", i3, i4);
  Serial.println(displayBuf);
  lcd.setCursor(9, 1);
  lcd.print(displayBuf);

  // Serial.println("time,temp1Up,temp1Bottom,temp2Up,temp2Bottom");
}




