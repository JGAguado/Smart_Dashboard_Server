#ifndef SERIAL_CONFIG_H
#define SERIAL_CONFIG_H

// ESP32-S2 Serial Configuration
// Use hardware UART for reliable development workflow
// Connect USB-to-serial adapter to GPIO 43 (TX) and GPIO 44 (RX)

#include <HardwareSerial.h>

// Redirect Serial to Serial1 (hardware UART on pins 43/44)
#define Serial Serial1

// Initialize hardware serial on GPIO 43 (TX) and 44 (RX)
inline void initSerial() {
    Serial1.begin(115200, SERIAL_8N1, 44, 43); // RX=44, TX=43
}

#endif // SERIAL_CONFIG_H
