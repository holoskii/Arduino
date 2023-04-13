#include <MAX6675_Thermocouple.h>

// #include <LiquidCrystal_I2C.h>
// LiquidCrystal_I2C lcd(0x27, 20, 4);

// MAX6675_Thermocouple thermocouple2(4, 5, 6); // 2 - GND, 3 - 5V, SCK, CS, SO

class Timer {
public:
    void start(unsigned long duration) {
        mStartTime = millis();
        mDuration = duration;
    }

    bool isExpired() {
        if(mDuration + mStartTime >= millis())
            return true;
        return false;
    } 

private:
    unsigned long mStartTime = 0;
    unsigned long mDuration = 0;
};

class Controller {
public:
    Controller(int tcGND, int tc5V, int tcSCK, int tcCS, int tcSO, int irelayControlPin, int irelayGroundPin)
    : tcGNDpin(tcGND), tc5Vpin(tc5V), thermocouple(tcSCK, tcCS, tcSO), relayControlPin(irelayControlPin), relayGroundPin(irelayGroundPin) {
        
    }

    void setup() {
        // setup relay
        pinMode(relayControlPin, OUTPUT);
        pinMode(relayGroundPin, OUTPUT);
        digitalWrite(relayControlPin, LOW);
        digitalWrite(relayGroundPin, LOW);

        // setup thermocouple
        pinMode(tcGNDpin, OUTPUT);
        pinMode(tc5Vpin, OUTPUT); 
        digitalWrite(tcGNDpin, LOW);
        digitalWrite(tc5Vpin, HIGH);
    }

    void loop() {
        currentTime = millis();
        pollLogic();
        pollRelay();
    }

private:
    // Logic
    unsigned long currentTime = 0;
    int controlValue = 0; // [0..1000], represents how ms in seconds relay will be ON
    int previousError = 0;
    int targetTemp = 400;
    double kp = 0.02, kd = 0.20;


    // Thermocouple
    static constexpr int NUM_TEMP_READS = 3;
    static constexpr int TEMP_READ_INTERVAL = 333;
    int readings[NUM_TEMP_READS + 2] = { 0 };
    int readingIndex = 0;
    unsigned long nextReadTime = 0;
    int tcGNDpin;
    int tc5Vpin;
    MAX6675_Thermocouple thermocouple;

    // Relay
    int relayControlPin;
    int relayGroundPin;
    bool relayState = false;
    unsigned long relayCycleStart = 0;
    unsigned long relayPollTime = 0;

    void pollLogic() {
        if(currentTime < nextReadTime)
            return;

        nextReadTime += TEMP_READ_INTERVAL;

        int temp = int(thermocouple.readCelsius() * 100); 
        readings[readingIndex] = temp;
        readingIndex = (readingIndex + 1) % NUM_TEMP_READS;

        
        Serial.println()

        if(readingIndex != 0)
            return;

        int averageTemp = calculateAverageTemp();
        controlValue = calculateControlValue(averageTemp);
        relayCycleStart = currentTime;
    }

     int calculateAverageTemp() {
        int sum = 0;
        for (int i = 0; i < NUM_TEMP_READS; i++) {
            sum += readings[i];
        }
        return sum / NUM_TEMP_READS;
    }

    int calculateControlValue(int temperature) {
        int error = targetTemp - temperature;
        int deriv = error - previousError;
        previousError = error;
        
        double cv = (kp * double(error)) + (kd * double(deriv));
        if (cv < 0.0) cv = 0.0;
        if (cv > 0.0 && cv < 0.05) cv = 0.0;
        if (cv > 1.0) cv = 1.0;
        if (cv < 1.0 && cv > 0.95) cv = 1.0;

        return 500;
        // return (int)(1000.0 * cv);
    }

    void pollRelay() {
        // Only poll once a millisecond
        if(currentTime == relayPollTime)
            return;
        relayPollTime = currentTime;

        unsigned long elapsedCycleTime = currentTime - relayCycleStart;
        relayState = (elapsedCycleTime < controlValue);

        relayState = true;
        if(elapsedCycleTime >= controlValue) {
            relayState = false;
        }
        else if (elapsedCycleTime >= 1000) {
            Serial.println("Overshoot");
            relayState = controlValue == 1000;
        }

        digitalWrite(relayControlPin, relayState ? HIGH : LOW);
    }
};

Controller controllerSubstr1(8, 9, 10, 11, 12, 22, 23);



void setup() {
    // setup serial
    Serial.begin(9600);
    Serial.println("\n\n\n\n\nSetup");

    // setup LCD
    // lcd.init();
    // lcd.backlight();
    // lcd.print("Hello world");
}

void loop() {
    controllerSubstr1.loop();
}

#if 0

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


#endif

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



