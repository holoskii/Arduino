#include <MAX6675_Thermocouple.h>

// ############################################## USER SET VARIABLES
static constexpr int        SUBSTRATE_TEMP = 420;
static constexpr float      SUBSTRATE_KP   = 0.02;
static constexpr float      SUBSTRATE_KD   = 0.50;

static constexpr int        SOURCE_TEMP = 480;
static constexpr float      SOURCE_KP   = 0.02;
static constexpr float      SOURCE_KD   = 0.50;

static constexpr bool       TRACE_ENABLED = true;
// ############################################## USER SET VARIABLES


// For more predictable logic calculations, use one time for each loop call
unsigned long currentTime = 0;
static constexpr int NUM_TEMP_READS = 4;
static constexpr int TEMP_READ_INTERVAL = 1000 / NUM_TEMP_READS;

inline int ip(float d) { return (int)d; }
inline int fp(float d) { return (int)((d - (int)d) * 100); }

// Controls PID, relays and thermocouples. 2 for reactor, one for both source and substrate
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

    // Logic
    int controlValue = 0; // [0..1000], represents how ms in seconds relay will be ON
    float previousError = 0;
    const int targetTemp;
    const float kp, kd;

    // Thermocouple
    float readings[NUM_TEMP_READS] = { 0 };
    int readingIndex = 0;
    const int tcGNDpin;
    const int tc5Vpin;
    const MAX6675_Thermocouple thermocouple;

    // Relay
    const int relayControlPin;
    const int relayGroundPin;
    bool relayState = false;

    bool pollLogic() {
        // Read temperature multiple times and find average to reduce noise
        const float temp = thermocouple.readCelsius(); 
        readings[readingIndex] = temp;
        readingIndex = (readingIndex + 1) % NUM_TEMP_READS;

        if(readingIndex != 0)
            return false;

        const float averageTemp = calculateAverageTemp();
        controlValue = calculateControlValue(averageTemp);
        return true;
    }

     float calculateAverageTemp() {
        float sum = 0;
        for (int i = 0; i < NUM_TEMP_READS; i++) {
            sum += readings[i];
        }
        return sum / NUM_TEMP_READS;
    }

    float temperature = 0, error = 0, deriv = 0, p = 0, d = 0, uncappedCV = 0, cv = 0;

    int calculateControlValue(float inTemperature) {
        // Save all these intermediate values to trace them
        temperature = inTemperature;
        error = targetTemp - temperature;
        deriv = error - previousError;
        previousError = error;
        
        p = kp * error;
        d = kd * deriv;
        uncappedCV = p + d;

        cv = min(1.0, max(0.0, uncappedCV));

        // Switch time is 10 ms, so avoid any time intervals < 10ms
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

// Manages 2 controllers, sends data through serial
class Reactor {
public:
    static const size_t serialBufLen = 1024;
    char serialBuf[serialBufLen];

    Controller substrateController {2, 3,  4,  5,  6, 22, 23, SUBSTRATE_TEMP, SUBSTRATE_KP, SUBSTRATE_KD}; // Substrate
    Controller sourceController    {8, 9, 10, 11, 12, 24, 25, SOURCE_TEMP,    SOURCE_KP,    SOURCE_KD   }; // Source

    unsigned long relayPollTime = 0;
    unsigned long nextReadTime = 0;
    unsigned long relayCycleStart = 0;

    void setup() {
        substrateController.setup();
        sourceController.setup();
    }

    void loop() {
        currentTime = millis();

        if(currentTime >= nextReadTime) {
            nextReadTime += TEMP_READ_INTERVAL;
            
            substrateController.pollLogic();
            bool calcLogic = sourceController.pollLogic();

            // Print only if logic was recalculated
            if(calcLogic) {
                relayCycleStart = currentTime;

                int pos = snprintf(serialBuf, serialBufLen
                    , "INFO: %lu,"
                      "%d.%02d,%d,"
                      "%d.%02d,%d\n" 
                    , currentTime / 1000
                    , ip(substrateController.temperature), fp(substrateController.temperature), int(substrateController.cv * 100)
                    , ip(sourceController.temperature), fp(sourceController.temperature), int(sourceController.cv * 100));

                if(TRACE_ENABLED) {
                    // Some code repetition
                    pos += snprintf(serialBuf + pos, serialBufLen - pos
                        , "TRACE1: ERR=%3d P=%3d D=%3d "
                          "uCV=%3d CV=%3d T=%3d, "
                        , ip(substrateController.error), int(substrateController.p * 100), int(substrateController.d * 100)
                        , int(substrateController.uncappedCV * 100), int(substrateController.cv * 100), ip(substrateController.temperature));
                            
                    pos += snprintf(serialBuf + pos, serialBufLen - pos
                        , "TRACE2: ERR=%3d P=%3d D=%3d "
                          "uCV=%3d CV=%3d T=%3d"
                        , ip(sourceController.error), int(sourceController.p * 100), int(sourceController.d * 100)
                        , int(sourceController.uncappedCV * 100), int(sourceController.cv * 100), ip(sourceController.temperature));
                }

                // Try to send all the info in one buffer to avoid flickering in receiving terminal
                Serial.println(serialBuf);
            }
        }

        // Only poll relay once a millisecond
        if(currentTime != relayPollTime) {
            relayPollTime = currentTime;
            substrateController.pollRelay(currentTime - relayCycleStart);
            sourceController.pollRelay(currentTime - relayCycleStart);
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


