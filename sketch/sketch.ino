#include <MAX6675_Thermocouple.h>
#include <assert.h>

// ##### USER SET VARIABLES
#include "parameters.h"

#define ENABLE_TIMER 1

inline int ip(double d) { return (int)d; }
inline int fp(double d) { return (int)((d - (int)d) * 100); }
enum class TimerState { OFF, STARTED, ENDED };

static constexpr int NUM_TEMP_READS = 4;
static constexpr int TEMP_READ_INTERVAL = 1000 / NUM_TEMP_READS;

unsigned long currentTime = 0;  // For more predictable logic calculations, update one time for each loop call

/**
 * @class Controller
 * @brief This class represents a controller for PID, relays, and thermocouples.
 * A Reactor object has two controllers, one for the source and one for the substrate.
 */
class Controller {
public:
    Controller(
        int tcGNDpin, int tc5Vpin, int tcSCK, int tcCS, int tcSO
        , int relayControlPin, int relayGroundPin
        , int targetTemp, double tempOffet, double kp, double kd)
    : tcGNDpin(tcGNDpin), tc5Vpin(tc5Vpin), thermocouple(tcSCK, tcCS, tcSO)
    , relayControlPin(relayControlPin), relayGroundPin(relayGroundPin)
    , targetTemp(targetTemp), tempOffet(tempOffet), kp(kp), kd(kd) {}

    // #################### FUNCTIONS ####################

    /**
     * @brief Set up the pins for the controller
     */
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

    /**
     * @brief Poll logic state and calculate control value
     * @return True if logic was recalculated, otherwise false
     */
    bool pollLogic(bool depositionEnded) {
        // Read temperature multiple times and find average to reduce noise
        const double temp = thermocouple.readCelsius(); 
        readings[readingIndex] = temp;
        readingIndex = (readingIndex + 1) % NUM_TEMP_READS;

        if(readingIndex != 0)
            return false;

        const double averageTemp = calculateAverageTemp();
        controlValue = calculateControlValue(averageTemp, depositionEnded);
        return true;
    }

     double calculateAverageTemp() {
        double sum = 0;
        for (int i = 0; i < NUM_TEMP_READS; i++) {
            sum += readings[i];
        }
        return sum / NUM_TEMP_READS;
    }

    /**
     * @brief Poll the state of the relay
     * @param elapsedCycleTime The elapsed cycle time
     */
    void pollRelay(unsigned long elapsedCycleTime) {
        relayState = (elapsedCycleTime < controlValue);

        if (elapsedCycleTime >= 1000) {
            Serial.print("Overshoot\nOvershoot\nOvershoot\n");
            relayState = controlValue == 1000;
        }

        digitalWrite(relayControlPin, relayState ? HIGH : LOW);
    }

private:
    /**
     * @brief Calculate the average temperature from the stored readings
     * @return The average temperature
     */
    int calculateControlValue(double inTemperature, bool depositionEnded) {
        // Save all these intermediate values to trace them
        temperature = inTemperature;
        error = targetTemp + tempOffet - temperature;
        deriv = error - previousError;
        previousError = error;
        
        p = kp * error;
        d = kd * deriv;
        uncappedCV = p + d;
        cv = uncappedCV;

        if(depositionEnded)
            cv = 0;

        // Switch time is 10 ms, so avoid any time intervals < 10ms
        if (cv < 0.01) cv = 0.0;
        if (cv > 0.99) cv = 1.0;

        return (int)(1000.0 * cv);
    }

    // #################### VARIABLES ####################
public:
    // Intermediate variables, used for monitoring
    double temperature = 0;
    double error = 0;
    double deriv = 0;
    double p = 0;
    double d = 0;
    double uncappedCV = 0;
    double cv = 0;

private:
    // Logic
    int controlValue = 0; // [0..1000], represents how ms in seconds relay will be ON
    double previousError = 0;
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
};

/**
 * @class Reactor
 * @brief This class represents a real reactor setup. 
 * It manages two separate heaters: one for the substrate and one for the source.
 */
class Reactor {
public:
    /**
     * @brief Setup the reactor
     */
    void setup() {
        sendParameters();
        substrateController.setup();
        sourceController.setup();
    }

    /**
     * @brief Send user parameters of the reactor setup to the serial port
     */
    void sendParameters() {
        int pos = snprintf(serialBuf, serialBufLen
            , "START: Substrate: T=(%3d+%2d) PD=(%d.%02d,%d.%02d); "
                "Source: T=(%3d+%2d) PD=(%d.%02d,%d.%02d); " 
                "TIMER: %lus\n\n"
            , SUBSTRATE_TEMP, SUBSTRATE_TEMP_OFFSET, ip(SUBSTRATE_KP), fp(SUBSTRATE_KP), ip(SUBSTRATE_KD), fp(SUBSTRATE_KD)
            , SOURCE_TEMP, SOURCE_TEMP_OFFSET, ip(SOURCE_KP), fp(SOURCE_KP), ip(SOURCE_KD), fp(SOURCE_KD)
            , DEPOSITION_TIME_MS / 1000);
        assert(pos < serialBufLen);
        Serial.write(serialBuf, pos);
        Serial.flush(); 
    }

    /**
     * @brief Main reactor loop. Limits polling to once a millisecond
     */
    void loop() {
        currentTime = millis();

        if(currentTime >= nextReadTime) {
            nextReadTime += TEMP_READ_INTERVAL;
            
            substrateController.pollLogic(timerState == TimerState::ENDED);
            bool calcLogic = sourceController.pollLogic(timerState == TimerState::ENDED);

            // Send data only if logic was recalculated
            if(calcLogic) {
                relayCycleStart = currentTime;

#if ENABLE_TIMER
                if (timerState == TimerState::OFF) {
                    if (sourceController.temperature + 5 >= SOURCE_TEMP && abs(sourceController.deriv) < 50) {
                        depositionStartTime = currentTime;
                        depositionEndTime = currentTime + DEPOSITION_TIME_MS;
                        timerState = TimerState::STARTED;
                    }
                } else if (timerState == TimerState::STARTED) {
                    if (currentTime >= depositionEndTime) {
                        timerState = TimerState::ENDED;
                    }
                }
#endif

                sendData();
            }
        }

        // Only poll relay once a millisecond
        if(currentTime != relayPollTime) {
            relayPollTime = currentTime;
            substrateController.pollRelay(currentTime - relayCycleStart);
            sourceController.pollRelay(currentTime - relayCycleStart);
        }
    }

    /**
     * @brief Send full reactor data to the serial port
     */
    void sendData() {
        int pos = snprintf(serialBuf, serialBufLen
            , "INFO: %lu,"
                "%d.%02d,%d,"
                "%d.%02d,%d\n" 
            , currentTime / 1000
            , ip(substrateController.temperature), fp(substrateController.temperature), int(substrateController.cv * 100)
            , ip(sourceController.temperature), fp(sourceController.temperature), int(sourceController.cv * 100));

        // Some code repetition
        pos += snprintf(serialBuf + pos, serialBufLen - pos
            , "TRACE: 1 SUBSTR   ERR=%3d   P=%3d   D=%3d   "
                "uCV=%3d   CV=%3d   T=%3d\n"
            , ip(substrateController.error), int(substrateController.p * 100), int(substrateController.d * 100)
            , int(substrateController.uncappedCV * 100), int(substrateController.cv * 100), ip(substrateController.temperature));
                
        pos += snprintf(serialBuf + pos, serialBufLen - pos
            , "TRACE: 2 SOURCE   ERR=%3d   P=%3d   D=%3d   "
                "uCV=%3d   CV=%3d   T=%3d\n"
            , ip(sourceController.error), int(sourceController.p * 100), int(sourceController.d * 100)
            , int(sourceController.uncappedCV * 100), int(sourceController.cv * 100), ip(sourceController.temperature));

#if ENABLE_TIMER
        // Timer debugging
        // pos += snprintf(serialBuf + pos, serialBufLen - pos
        //                 , "TIMER FULL: DEPOSITION_TIME_MS=%lu, depositionStartTime_ms=%lu, depositionEndTime_ms=%lu, currentTime_ms=%lu\n"
        //                 , DEPOSITION_TIME_MS, depositionStartTime, depositionEndTime, currentTime);

        if (timerState == TimerState::OFF) {
            pos += snprintf(serialBuf + pos, serialBufLen - pos, "TIMER OFF\n");
        } else if (timerState == TimerState::STARTED) {
            pos += snprintf(serialBuf + pos, serialBufLen - pos, "TIMER STARTED:  time left = %lu sec\n", (depositionEndTime - currentTime) / 1000);
        } else {
            pos += snprintf(serialBuf + pos, serialBufLen - pos, "TIMER ENDED\n");
        }
#endif

        pos += snprintf(serialBuf + pos, serialBufLen - pos, "\n");

        // Try to send all the info in one buffer to avoid flickering in receiving terminal
        assert(pos < serialBufLen);
        Serial.write(serialBuf, pos);
        Serial.flush(); 
    }

    // #################### VARIABLES ####################
private:
    Controller substrateController {2, 3,  4,  5,  6, 22, 23, SUBSTRATE_TEMP, SUBSTRATE_TEMP_OFFSET, SUBSTRATE_KP, SUBSTRATE_KD}; // Substrate
    Controller sourceController    {8, 9, 10, 11, 12, 24, 25, SOURCE_TEMP,    SOURCE_TEMP_OFFSET,    SOURCE_KP,    SOURCE_KD   }; // Source

    static const size_t serialBufLen = 2048;
    char serialBuf[serialBufLen];

    unsigned long relayPollTime = 0;
    unsigned long nextReadTime = 0;
    unsigned long relayCycleStart = 0;

    // Timer variables
    TimerState timerState = TimerState::OFF;
    unsigned long depositionStartTime = 0;
    unsigned long depositionEndTime = 0;
};

Reactor r{};

void setup() {
    Serial.begin(9600);
    r.setup();
}

void loop() {
    r.loop();
}


