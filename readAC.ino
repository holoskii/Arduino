#include "stdio.h"

int analogPin = A3;

uint16_t get_max_basic() {
	uint16_t maxV = 0;
	for(uint8_t i = 0; i < 100; i++) {
		uint16_t v = analogRead(analogPin); // read from analog channel 3 (A3)
		if(maxV < v)
			maxV = v;
		delayMicroseconds(100);
	}
	return maxV;
}

// AC 50 Hz -> need to measure for at least 20 ms
uint16_t get_max_smart() {
	uint64_t timeStart = millis();
	uint16_t maxV = 0;
	while(millis() < timeStart + 20) {
		uint16_t v = analogRead(analogPin);
		if(maxV < v)
			maxV = v;
		delayMicroseconds(100);
	}
	return maxV;
}

void setup(void) {
	analogReference(INTERNAL1V1); // set ADC positive reference voltage to 1.1V (internal)
	Serial.begin(9600);
	Serial.println("\n\n\n\n\nSetup");
}

void loop() {
	uint32_t getMax = get_max_basic();
	uint32_t vMax = getMax * 1100/1023;
	uint32_t v = vMax / sqrt(2);
	
	char buf[64];
	snprintf("getMax: %5u, vMax: %5u, v: %5u\n", getMax, vMax, v);
	delay(100);
}


// Arduino Frequence = 16 MHz


