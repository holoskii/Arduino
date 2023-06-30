#include <MAX6675_Thermocouple.h>

// ############################################## USER SET VARIABLES
//                          SUBSTRATE
static constexpr double     SUBSTRATE_POWER_LIMIT = 1.0;
static constexpr int        SUBSTRATE_TEMP_OFFSET = 5; // increases target temp for PID calculations
static constexpr int        SUBSTRATE_TEMP = 400;
static constexpr double     SUBSTRATE_KP   = 0.02;
static constexpr double     SUBSTRATE_KD   = 0.60;

//                          SOURCE
static constexpr double     SOURCE_POWER_LIMIT = 1.0;
static constexpr int        SOURCE_TEMP_OFFSET = 15;
static constexpr int        SOURCE_TEMP = 430;
static constexpr double     SOURCE_KP   = 0.02;
static constexpr double     SOURCE_KD   = 0.40;

// COMMON
static constexpr long       DEPOSITION_TIME_MS = 10 * 60 * 1000;
static constexpr bool       DEBUG_ENABLED = true;
// ############################################## USER SET VARIABLES


inline int ip(double d) { return (int)d; }
inline int fp(double d) { return (int)((d - (int)d) * 100); }

static constexpr int NUM_TEMP_READS = 4;
static constexpr int TEMP_READ_INTERVAL = 1000 / NUM_TEMP_READS;

unsigned long currentTime     = 0;  // For more predictable logic calculations, use one time for each loop call
bool          depositionEnded = false;

// Controls PID, relays and thermocouples. 2 for reactor, one for both source and substrate
class Controller {
public:
    Controller(
        int tcGNDpin, int tc5Vpin, int tcSCK, int tcCS, int tcSO
        , int relayControlPin, int relayGroundPin, double powerLimit
        , int targetTemp, double tempOffet, double kp, double kd)
    : tcGNDpin(tcGNDpin), tc5Vpin(tc5Vpin), thermocouple(tcSCK, tcCS, tcSO)
    , relayControlPin(relayControlPin), relayGroundPin(relayGroundPin), powerLimit(powerLimit)
    , targetTemp(targetTemp), tempOffet(tempOffet), kp(kp), kd(kd) {}

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
    double previousError = 0;
    const double powerLimit;
    const int targetTemp;
    const double tempOffet;
    const double kp, kd;

    // Thermocouple
    double readings[NUM_TEMP_READS] = { 0 };
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
        const double temp = thermocouple.readCelsius(); 
        readings[readingIndex] = temp;
        readingIndex = (readingIndex + 1) % NUM_TEMP_READS;

        if(readingIndex != 0)
            return false;

        const double averageTemp = calculateAverageTemp();
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
        // Save all these intermediate values to trace them
        temperature = inTemperature;
        error = targetTemp + tempOffet - temperature;
        deriv = error - previousError;
        previousError = error;
        
        p = kp * error;
        d = kd * deriv;
        uncappedCV = p + d;

        if (depositionEnded)
            return 0;

        cv = min(powerLimit, max(0.0, uncappedCV));

        // Switch time is 10 ms, so avoid any time intervals < 10ms
        if (cv < 0.01) cv = 0.0;
        if (cv > 0.99) cv = 1.0;

        return (int)(1000.0 * cv);
    }

    void pollRelay(unsigned long elapsedCycleTime) {
        relayState = (elapsedCycleTime < controlValue);

        if (elapsedCycleTime >= 1000) {
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

    Controller substrateController {2, 3,  4,  5,  6, 22, 23, SUBSTRATE_POWER_LIMIT, SUBSTRATE_TEMP, SUBSTRATE_TEMP_OFFSET, SUBSTRATE_KP, SUBSTRATE_KD}; // Substrate
    Controller sourceController    {8, 9, 10, 11, 12, 24, 25, SOURCE_POWER_LIMIT,    SOURCE_TEMP,    SOURCE_TEMP_OFFSET,    SOURCE_KP,    SOURCE_KD   }; // Source

    unsigned long relayPollTime = 0;
    unsigned long nextReadTime = 0;
    unsigned long relayCycleStart = 0;

    bool depositionStarted = false;
    unsigned long depositionStartTime = 0;

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

                // if (!depositionStarted) {
                //     if (sourceController.temperature >= sourceController.targetTemp * 0.99 && abs(sourceController.deriv) < 50) {
                //         depositionStarted = true;
                //         depositionStartTime = currentTime;
                //     }
                // }
                // else {
                //     if (currentTime - depositionStartTime > DEPOSITION_TIME_MS) {
                //         depositionEnded = true;
                //     }
                // }

                int pos = snprintf(serialBuf, serialBufLen
                    , "INFO: %lu,"
                      "%d.%02d,%d,"
                      "%d.%02d,%d\n" 
                    , currentTime / 1000
                    , ip(substrateController.temperature), fp(substrateController.temperature), int(substrateController.cv * 100)
                    , ip(sourceController.temperature), fp(sourceController.temperature), int(sourceController.cv * 100));

                if(DEBUG_ENABLED) {
                    // Some code repetition
                    pos += snprintf(serialBuf + pos, serialBufLen - pos
                        , "TRACE1(SUBSTR): ERR=%3d P=%3d D=%3d "
                          "uCV=%3d CV=%3d T=%3d\n"
                        , ip(substrateController.error), int(substrateController.p * 100), int(substrateController.d * 100)
                        , int(substrateController.uncappedCV * 100), int(substrateController.cv * 100), ip(substrateController.temperature));
                            
                    pos += snprintf(serialBuf + pos, serialBufLen - pos
                        , "TRACE2(SOURCE): ERR=%3d P=%3d D=%3d "
                          "uCV=%3d CV=%3d T=%3d\n"
                        , ip(sourceController.error), int(sourceController.p * 100), int(sourceController.d * 100)
                        , int(sourceController.uncappedCV * 100), int(sourceController.cv * 100), ip(sourceController.temperature));
                    
                    pos += snprintf(serialBuf + pos, serialBufLen - pos
                        , "TIMER: started=%d, ended=%d, started_at=%lu"
                        , int(depositionStarted), int(depositionEnded), depositionStartTime);
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


