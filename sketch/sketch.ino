#if 0

ls -la /dev/ttyACM0 && sudo chmod a+rw /dev/ttyACM0 && ls -la /dev/ttyACM0 

~/Arduino-IDE/arduino-cli compile --fqbn arduino:avr:mega ~/Arduino/sketch && ~/Arduino-IDE/arduino-cli upload ~/Arduino/sketch --fqbn arduino:avr:mega --port /dev/ttyACM0 --verbose

cat -v /dev/ttyACM0 | tee ~/Arduino/out.txt

# 4. Graph
cd ~/Arduino && python3 main.py out.txt

#endif


#include <LiquidCrystal_I2C.h>
#include <MAX6675_Thermocouple.h>

// Global variables
LiquidCrystal_I2C lcd(0x27, 20, 4);
MAX6675_Thermocouple thermocouple1(10, 11, 12); // 8 - GND, 9 - 5V, SCK, CS, SO
MAX6675_Thermocouple thermocouple2(4, 5, 6); // 2 - GND, 3 - 5V, SCK, CS, SO

bool useRelay1 = true; 
// 1 = SUBSTRATE
// 2 = SOURCE



// settable parameters
double target_sample_temp = 400;
double kp = 0.02, ki = 0, kd = 0.20;


int relay1Pin = 22;
int relay1Ground = 23;
int relay2Pin = 24;
int relay2Ground = 25;


double temp1, temp2; // Thermal pair readings
unsigned long currentTime = 0; // Time in seconds since the start
unsigned int controlValue = 0; // from 0 to 1000


void setup() {
    // setup relay1
    pinMode(relay1Pin, OUTPUT);
    pinMode(relay1Ground, OUTPUT);
    digitalWrite(relay1Pin, LOW);
    digitalWrite(relay1Ground, LOW);

    // setup relay2
    pinMode(relay2Pin, OUTPUT);
    pinMode(relay2Ground, OUTPUT);
    digitalWrite(relay2Pin, LOW);
    digitalWrite(relay2Ground, LOW);

    // setup serial
    Serial.begin(9600);
    Serial.println("\n\n\n\n\nSetup");

    // setup LCD
    lcd.init();
    lcd.backlight();
    lcd.print("Hello world");

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
}

unsigned long iterationStart = 0;
bool relayState = false;
void pollRelay() {
    if (millis() < iterationStart + controlValue)
        relayState = true;
    else if (millis() < iterationStart + 1000)
        relayState = false;
    else {
        iterationStart = iterationStart + 1000;
        relayState = true;
    }

    // RELAY SWITCH
    /*if(useRelay1)
        digitalWrite(relay1Pin, relayState ? HIGH : LOW);
    else 
        digitalWrite(relay2Pin, relayState ? HIGH : LOW);*/
    digitalWrite(relay1Pin, relayState ? HIGH : LOW);


}

void pollInput() {
    temp1 = thermocouple1.readCelsius(); 
    temp2 = thermocouple2.readCelsius(); 
}


// PID consts
constexpr int integral_count = 3;
double* integral_arr         = nullptr;
double prev_err              = 0;

double error, deriv;

double tmp1 = 0.0;
void pollLogic() {
    /*
    controlValue = 50 * currentTime;
    if (controlValue < 10) 
        controlValue = 0;
    if (controlValue > 990) 
        controlValue = 1000;
    
    if (controlValue < 0)
        controlValue = 0;
    if (controlValue > 1000)
        controlValue = 1000;
    */

    // PID calculations
    if(useRelay1)
        error = target_sample_temp - temp1;
    else 
        error = target_sample_temp - temp2;
    
    deriv = error - prev_err;


    
    tmp1 = (kp * error) + (kd * deriv);
    if(tmp1 < 0.0) tmp1 = 0.0;
    if(tmp1 > 1.0) tmp1 = 1.0;
    controlValue = (int)(1000.0 * tmp1);
    prev_err = error;
}

constexpr size_t lineBufSize = 17;
char lineBuf[lineBufSize];
char serialBuf[255];
inline int ip(double d) { return (int)d; }
inline int fp(double d) { return (int)((d - (int)d) * 100); } 
void pollOutput() {
    // LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    snprintf(lineBuf, lineBufSize, "Time %02lu:%02lu", currentTime / 60LU, currentTime % 60LU);
    lcd.print(lineBuf);
    lcd.setCursor(0, 1);
    snprintf(lineBuf, lineBufSize, "T1: %3d.%02d", ip(temp1), fp(temp1));
    lcd.print(lineBuf);
    lcd.setCursor(0, 2);
    snprintf(lineBuf, lineBufSize, "T2: %3d.%02d", ip(temp2), fp(temp2));
    lcd.print(lineBuf);

    // Serial
    currentTime = millis() / 1000;
    snprintf(serialBuf, 255, "D T1=%d.%02d,T2=%d.%02d,time=%lu,control=%u P=%d D=%d, error=%d", 
            ip(temp1), fp(temp1), ip(temp2), fp(temp2), currentTime, controlValue / 10, int(kp * error * 100.0), int(kd * deriv * 100.0), int(error));
    Serial.println(serialBuf);
}


unsigned long pollTime = 0;
void loop() {
    pollRelay(); // <- fast switching, no delays here
    
    if(pollTime <= millis()) {
        pollTime += 1000;
        pollInput();
        pollLogic();
        pollOutput();
    }
}




#if 0
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
#endif



