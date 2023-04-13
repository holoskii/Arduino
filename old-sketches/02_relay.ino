#if 0

# 1. Permission
ls -la /dev/ttyACM0 && sudo chmod a+rw /dev/ttyACM0 && ls -la /dev/ttyACM0

# 2. Compile && Upload
~/Arduino-IDE/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch && ~/Arduino-IDE/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose

# 3. Read
cat -v /dev/ttyACM0 | tee ~/Arduino/out.txt


# 4. Graph
cd ~/Arduino && python3 main.py out.txt

#endif

#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4);

void setup() {
    pinMode(13, OUTPUT);    // sets the digital pin 13 as output

    Serial.begin(9600);
    Serial.println("\n\n\n\n\nSetup");

    // setup LCD
    lcd.init();
    lcd.backlight();
    lcd.print("Hello world");
    
    delay(500);
}

char buf[255];

unsigned long curTime = 0;
unsigned long measureAtMsec = 1500;
unsigned long screenUpdateInterval = 1000;

// Display interaction (buffers and printing)
constexpr size_t lineBufSize = 17;
char lineBuf[lineBufSize];


unsigned long switchAtMsec = 1000;
unsigned long switchUpdateInterval = 5000;
bool switchState = 0;


void loop() {
    if(switchAtMsec <= millis()) {
        switchAtMsec += switchUpdateInterval;
        curTime = millis() / 1000;

        switchState ^= 1;
        digitalWrite(13, switchState); // sets the digital pin 13 on

        snprintf(buf, 255, "S %d,%lu", switchState, curTime);
        Serial.println(buf);

        lcd.clear();
        lcd.setCursor(0, 0);
        snprintf(lineBuf, lineBufSize, "Time %02lu:%02lu", curTime / 60LU, curTime % 60LU);
        lcd.print(lineBuf);

        lcd.setCursor(0, 1);
        snprintf(lineBuf, lineBufSize, "S: %d", switchState);
        lcd.print(lineBuf);
    }
}



