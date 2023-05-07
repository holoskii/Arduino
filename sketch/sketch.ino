#include <MAX6675_Thermocouple.h>

// #############################
// USER SET VARIABLES
static constexpr int        SUBSTRATE_TEMP = 420;
static constexpr double     SUBSTRATE_KP   = 0.02;
static constexpr double     SUBSTRATE_KD   = 0.50;

static constexpr int        SOURCE_TEMP = 480;
static constexpr double     SOURCE_KP   = 0.02;
static constexpr double     SOURCE_KD   = 0.50;
// #############################

unsigned long currentTime = 0;
char serialBuf[512]; 
static constexpr int NUM_TEMP_READS = 4;
static constexpr int TEMP_READ_INTERVAL = 1000 / NUM_TEMP_READS;

inline int ip(double d) { return (int)d; }
inline int fp(double d) { return (int)((d - (int)d) * 100); }


class Controller {
public:
    Controller(
        int tcGND, int tc5V, int tcSCK, int tcCS, int tcSO, 
        int irelayControlPin, int irelayGroundPin, 
        int itargetTemp, float ikp, float ikd)
    : tcGNDpin(tcGND), tc5Vpin(tc5V), thermocouple(tcSCK, tcCS, tcSO)
    , relayControlPin(irelayControlPin), relayGroundPin(irelayGroundPin)
    , targetTemp(itargetTemp), kp(ikp), kd(ikd) {}

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

public:
    // Logic
    int controlValue = 0; // [0..1000], represents how ms in seconds relay will be ON
    double previousError = 0;
    const int targetTemp;
    const double kp, kd;

    // Thermocouple
    double readings[NUM_TEMP_READS] = { 0 };
    int readingIndex = 0;
    const int tcGNDpin;
    const int tc5Vpin;
    const MAX6675_Thermocouple thermocouple;

    // Relay
    int relayControlPin;
    int relayGroundPin;
    bool relayState = false;

    bool pollLogic() {
        double tempDouble = thermocouple.readCelsius();
        double temp = tempDouble; 
        readings[readingIndex] = temp;
        readingIndex = (readingIndex + 1) % NUM_TEMP_READS;

        if(readingIndex != 0)
            return false;

        double averageTemp = calculateAverageTemp();
        controlValue = calculateControlValue(averageTemp);
        return true;
    }

     double calculateAverageTemp() {
        double sum = 0;
        for (int i = 0; i < NUM_TEMP_READS; i++) {
            sum += readings[i];
        }
        return sum / NUM_TEMP_READS;
    }

    double temperature = 0, error = 0, deriv = 0, p = 0, d = 0, uncappedCV = 0, cv = 0;

    int calculateControlValue(double inTemperature) {
        temperature = inTemperature;
        error = targetTemp - temperature;
        deriv = error - previousError;
        previousError = error;
        
        p = kp * error;
        d = kd * deriv;
        uncappedCV = p + d;

        cv = min(1.0, max(0.0, uncappedCV));

        if (cv < 0.01) cv = 0.0;
        if (cv > 0.99) cv = 1.0;

        return (int)(1000.0 * cv);
    }

    void pollRelay(unsigned long elapsedCycleTime) {
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

class Reactor {
public:
    Controller c1 {2, 3, 4, 5, 6, 22, 23, SUBSTRATE_TEMP, SUBSTRATE_KP, SUBSTRATE_KD}; // Substrate
    Controller c2 {8, 9, 10, 11, 12, 24, 25, SOURCE_TEMP, SOURCE_KP, SOURCE_KD}; // Source

    unsigned long relayPollTime = 0;
    unsigned long nextReadTime = 0;
    unsigned long relayCycleStart = 0;

    void setup() {
        c1.setup();
        c2.setup();
    }

    void loop() {
        currentTime = millis();

        if(currentTime >= nextReadTime) {
            nextReadTime += TEMP_READ_INTERVAL;
            
            c1.pollLogic();
            bool calcLogic = c2.pollLogic();

            if(calcLogic) {
                relayCycleStart = currentTime;

                snprintf(serialBuf, 512, "INFO: %lu,%d.%02d,%d,%d.%02d,%d" 
                    , currentTime / 1000, ip(c1.temperature), fp(c1.temperature), int(c1.cv * 100), ip(c2.temperature), fp(c2.temperature), int(c2.cv * 100));
                Serial.println(serialBuf);  

                snprintf(serialBuf, 512, "TRACE1: ERR=%3d P=%3d D=%3d uCV=%3d CV=%3d T=%3d, TRACE2: ERR=%3d P=%3d D=%3d uCV=%3d CV=%3d T=%3d"
                    , ip(c1.error),int(c1.p * 100), int(c1.d * 100), int(c1.uncappedCV * 100), int(c1.cv * 100), ip(c1.temperature) 
                    , ip(c2.error),int(c2.p * 100), int(c2.d * 100), int(c2.uncappedCV * 100), int(c2.cv * 100), ip(c2.temperature));
                Serial.println(serialBuf);
            }
        }


        // Only poll relay once a millisecond
        if(currentTime != relayPollTime) {
            relayPollTime = currentTime;
            c1.pollRelay(currentTime - relayCycleStart);
            c2.pollRelay(currentTime - relayCycleStart);
        }
    }
};

Reactor r{};

void setup() {
    Serial.begin(9600);
    Serial.println("\n\n\nStart");
    r.setup();
}

void loop() {
    r.loop();
}


