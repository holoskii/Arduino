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
#include <MAX6675_Thermocouple.h>

LiquidCrystal_I2C lcd(0x27, 20, 4);
MAX6675_Thermocouple thermocouple1(4, 5, 6); // 2 - GND, 3 - 5V, SCK, CS, SO
MAX6675_Thermocouple thermocouple2(10, 11, 12); // 8 - GND, 9 - 5V, SCK, CS, SO

void setup() {
    Serial.begin(9600);
    Serial.println("\n\n\n\n\nSetup");
    
    // setup thermocouple1
    pinMode(2, OUTPUT);
    pinMode(3, OUTPUT); 
    digitalWrite(2, LOW);
    digitalWrite(3, HIGH);

    // setup thermocouple2
    pinMode(8, OUTPUT);
    pinMode(9, OUTPUT);
    digitalWrite(8, LOW);
    digitalWrite(9, HIGH);

    // setup LCD
    lcd.init();
    lcd.backlight();
    lcd.print("Hello world");
    
    delay(500);
}

double c1, c2;
char buf[255];

unsigned long curTime = 0;
unsigned long measureAtMsec = 1500;
unsigned long screenUpdateInterval = 1000;
// unsigned long serialUpdateInterval = 1000;

// Display interaction (buffers and printing)
constexpr size_t lineBufSize = 17;
char lineBuf[lineBufSize];

inline int ip(double d) {
    return (int)d;
}

inline int fp(double d) {
    return (int)((d - (int)d) * 100);
} 

void loop() {
    if(measureAtMsec <= millis()) {
        measureAtMsec += screenUpdateInterval;
        curTime = millis() / 1000;
        c1 = thermocouple1.readCelsius(); 
        c2 = thermocouple2.readCelsius(); 
        snprintf(buf, 255, "D %d.%02d,%d.%02d,%lu", ip(c1), fp(c1), ip(c2), fp(c2), curTime);
        Serial.println(buf);

        lcd.clear();
        lcd.setCursor(0, 0);
        snprintf(lineBuf, lineBufSize, "Time %02lu:%02lu", curTime / 60LU, curTime % 60LU);
        lcd.print(lineBuf);
        lcd.setCursor(0, 1);
        snprintf(lineBuf, lineBufSize, "T1: %3d.%02d", ip(c1), fp(c1));
        lcd.print(lineBuf);
        lcd.setCursor(0, 2);
        snprintf(lineBuf, lineBufSize, "T2: %3d.%02d", ip(c2), fp(c2));
        lcd.print(lineBuf);
    }
}



