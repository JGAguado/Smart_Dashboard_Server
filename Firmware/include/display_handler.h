#ifndef DISPLAY_HANDLER_H
#define DISPLAY_HANDLER_H

#include "epd7in3f.h"
#include "qr_code.h"
#include "config.h"

class DisplayHandler {
public:
    DisplayHandler();
    ~DisplayHandler();
    
    bool initialize();
    void displayImage(const uint8_t* imageData, size_t dataSize);
    void showStatus(const char* message);
    void showSimpleMessage(const char* message);
    void showColorTest();
    void showConfigurationQR();
    void clear();
    void sleep();
    
private:
    EPD7in3f epd;
    bool initialized;
    
    // Convert RGB image data to e-paper format
    void convertImageData(const uint8_t* rgbData, size_t dataSize, uint8_t* epdData);
    uint8_t getClosestColor(uint8_t r, uint8_t g, uint8_t b);
    
    // QR code display functions
    void displayQRWithInstructions();
    void drawText(uint8_t* buffer, const char* text, int x, int y, int scale);
};

#endif // DISPLAY_HANDLER_H
