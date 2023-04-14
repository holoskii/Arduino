#include <MAX6675_Thermocouple.h>

char serialBuf[255]; 
int ip(double d) { return (int)d; }
int fp(double d) { return (int)((d - (int)d) * 100); }

class Controller {
public:
    Controller(int tcGND, int tc5V, int tcSCK, int tcCS, int tcSO, int irelayControlPin, int irelayGroundPin, int itargetTemp)
    : tcGNDpin(tcGND), tc5Vpin(tc5V), thermocouple(tcSCK, tcCS, tcSO), relayControlPin(irelayControlPin), relayGroundPin(irelayGroundPin), targetTemp(itargetTemp) {}

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
    double previousError = 0;
    int targetTemp;
    double kp = 0.02, kd = 0.50;


    // Thermocouple
    static constexpr int NUM_TEMP_READS = 4;
    static constexpr int TEMP_READ_INTERVAL = 1000 / NUM_TEMP_READS;
    double readings[NUM_TEMP_READS] = { 0 };
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

        double tempDouble = thermocouple.readCelsius();
        double temp = tempDouble; 
        readings[readingIndex] = temp;
        readingIndex = (readingIndex + 1) % NUM_TEMP_READS;

        if(readingIndex != 0)
            return;

        double averageTemp = calculateAverageTemp();
        controlValue = calculateControlValue(averageTemp);
        relayCycleStart = currentTime;
    }

     double calculateAverageTemp() {
        double sum = 0;
        for (int i = 0; i < NUM_TEMP_READS; i++) {
            sum += readings[i];
        }
        return sum / NUM_TEMP_READS;
    }

    int calculateControlValue(double temperature) {
        double error = targetTemp - temperature;
        double deriv = error - previousError;
        previousError = error;
        
        double p = kp * error;
        double d = kd * deriv;
        double uncappedCV = p + d;

        double cv = min(1.0, max(0.0, uncappedCV));

        if (cv < 0.01) cv = 0.0;
        if (cv > 0.99) cv = 1.0;

        snprintf(serialBuf, 255, "TRACE: ERR=%3d P=%3d D=%3d uCV=%3d CV=%3d T=%3d"
            , ip(error),int(p * 100), int(d * 100), int(uncappedCV * 100), int(cv * 100), ip(temperature), fp(temperature));
        Serial.print(serialBuf);

        snprintf(serialBuf, 255, "INFO: %lu,%d.%02d,%d"
            , currentTime / 1000, ip(temperature), fp(temperature), int(cv * 1000));
        Serial.print(serialBuf);


        return (int)(1000.0 * cv);
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
            Serial.print("Overshoot\nOvershoot\nOvershoot\n");
            relayState = controlValue == 1000;
        }

        digitalWrite(relayControlPin, relayState ? HIGH : LOW);
    }
};

Controller controllerSubstr1(2, 3, 4, 5, 6, 22, 23, 420);



void setup() {
    Serial.begin(9600);
    Serial.println("\n\n\n\n\nSetup");

    controllerSubstr1.setup();
}

void loop() {
    controllerSubstr1.loop();
}




// #include <LiquidCrystal_I2C.h>
// LiquidCrystal_I2C lcd(0x27, 20, 4);

// setup LCD
// lcd.init();
// lcd.backlight();
// lcd.print("Hello world");


