#include "display_handler.h"
#include "serial_config.h"  // Must be included before Arduino.h
#include <Arduino.h>

DisplayHandler::DisplayHandler() : initialized(false) {
}

DisplayHandler::~DisplayHandler() {
    if (initialized) {
        sleep();
    }
}

bool DisplayHandler::initialize() {
    Serial.println("Initializing e-paper display...");
    
    if (epd.init() != 0) {
        Serial.println("E-paper initialization failed");
        return false;
    }
    
    initialized = true;
    Serial.println("E-paper display initialized successfully");
    
    // Don't clear or display anything - keep display blank until image is fetched
    
    return true;
}

void DisplayHandler::clear() {
    if (!initialized) return;
    
    Serial.println("Clearing display...");
    epd.clear(EPD_7IN3F_WHITE);
}

void DisplayHandler::showStatus(const char* message) {
    if (!initialized) return;
    
    Serial.printf("Showing status: %s\n", message);
    
    // If this is configuration mode, show QR code
    if (strcmp(message, "Configuration Mode") == 0) {
        showConfigurationQR();
    } else {
        // For other statuses, show color blocks
        showColorTest();
    }
}

void DisplayHandler::showConfigurationQR() {
    if (!initialized) return;
    
    Serial.println("Displaying configuration QR code...");
    
    // Allocate buffer for e-paper data (800x480, 2 pixels per byte)
    size_t bufferSize = (DISPLAY_WIDTH * DISPLAY_HEIGHT) / 2;
    uint8_t* epaperBuffer = (uint8_t*)malloc(bufferSize);
    
    if (!epaperBuffer) {
        Serial.println("Failed to allocate buffer for QR display");
        showColorTest();
        return;
    }
    
    // Clear buffer with white background
    for (size_t i = 0; i < bufferSize; i++) {
        epaperBuffer[i] = 0x11;  // White pixels (2 pixels per byte)
    }
    
    // Generate QR code for WiFi connection
    const int qrSize = 41;  // 41x41 QR code
    uint8_t* qrData = (uint8_t*)malloc(qrSize * qrSize);
    
    if (qrData) {
        // Generate WiFi QR code
        QRCode::generateWiFiQR(AP_SSID, AP_PASSWORD, qrData, qrSize);
        
        // Convert and draw QR code on display (centered, scaled 8x)
        QRCode::convertToEPaperFormat(qrData, qrSize, epaperBuffer, 
                                     DISPLAY_WIDTH / 2, DISPLAY_HEIGHT / 2 - 50, 8);
        
        free(qrData);
    }
    
    // Add text instructions around the QR code
    drawText(epaperBuffer, "Smart Dashboard Setup", 200, 50, 2);
    drawText(epaperBuffer, "1. Scan QR code to connect to WiFi", 150, 380, 1);
    drawText(epaperBuffer, "2. Open browser to 192.168.4.1", 180, 410, 1);
    drawText(epaperBuffer, "3. Configure your settings", 220, 440, 1);
    
    // Display the buffer
    epd.display(epaperBuffer);
    
    free(epaperBuffer);
    Serial.println("Configuration QR code displayed");
}

void DisplayHandler::showSimpleMessage(const char* message) {
    if (!initialized) return;
    
    Serial.printf("Showing simple message: %s\n", message);
    
    // Allocate buffer for e-paper data (800x480, 2 pixels per byte)
    size_t bufferSize = (DISPLAY_WIDTH * DISPLAY_HEIGHT) / 2;
    uint8_t* epaperBuffer = (uint8_t*)malloc(bufferSize);
    
    if (!epaperBuffer) {
        Serial.println("Failed to allocate buffer for message display");
        return;
    }
    
    // Clear buffer with white background
    for (size_t i = 0; i < bufferSize; i++) {
        epaperBuffer[i] = 0x11;  // White pixels (2 pixels per byte)
    }
    
    // Calculate text position to center it
    int textLen = strlen(message);
    int textWidth = textLen * 6 * 2;  // 6 pixels per char * scale 2
    int x = (DISPLAY_WIDTH - textWidth) / 2;
    int y = DISPLAY_HEIGHT / 2 - 7;  // 7 pixels high text
    
    // Draw the message
    drawText(epaperBuffer, message, x, y, 2);
    
    // Display the buffer
    epd.display(epaperBuffer);
    
    free(epaperBuffer);
}

void DisplayHandler::showColorTest() {
    if (!initialized) return;
    
    Serial.println("Showing color test pattern...");
    epd.showColorBlocks();
}

void DisplayHandler::displayImage(const uint8_t* imageData, size_t dataSize) {
    if (!initialized) return;
    
    Serial.printf("Displaying image (%d bytes)...\n", dataSize);
    
    // Calculate expected size for 800x480 display
    // Each pixel uses 4 bits (2 pixels per byte)
    size_t expectedSize = (DISPLAY_WIDTH * DISPLAY_HEIGHT) / 2;
    
    if (dataSize < expectedSize) {
        Serial.printf("Warning: Image data too small (%d < %d)\n", dataSize, expectedSize);
        showStatus("Image Error: Size Mismatch");
        return;
    }
    
    // If the image data is already in the correct format, display it directly
    epd.display(imageData);
    
    Serial.println("Image displayed successfully");
}

void DisplayHandler::sleep() {
    if (!initialized) return;
    
    Serial.println("Putting display to sleep...");
    epd.sleep();
}

uint8_t DisplayHandler::getClosestColor(uint8_t r, uint8_t g, uint8_t b) {
    // Simple color mapping to 7-color e-paper display
    // This is a basic implementation - can be refined
    
    if (r < 50 && g < 50 && b < 50) return EPD_7IN3F_BLACK;
    if (r > 200 && g > 200 && b > 200) return EPD_7IN3F_WHITE;
    if (g > r && g > b) return EPD_7IN3F_GREEN;
    if (b > r && b > g) return EPD_7IN3F_BLUE;
    if (r > g && r > b) return EPD_7IN3F_RED;
    if (r > 150 && g > 150 && b < 100) return EPD_7IN3F_YELLOW;
    if (r > 150 && g > 100 && b < 100) return EPD_7IN3F_ORANGE;
    
    return EPD_7IN3F_WHITE; // Default
}

void DisplayHandler::convertImageData(const uint8_t* rgbData, size_t dataSize, uint8_t* epdData) {
    // Convert RGB image to e-paper format
    // This is a placeholder - real implementation would need proper image processing
    
    size_t pixelCount = DISPLAY_WIDTH * DISPLAY_HEIGHT;
    size_t epdByteCount = pixelCount / 2;
    
    for (size_t i = 0; i < epdByteCount && i * 6 < dataSize; i++) {
        // Process 2 pixels at a time (each uses 4 bits)
        uint8_t r1 = (i * 6 < dataSize) ? rgbData[i * 6] : 255;
        uint8_t g1 = (i * 6 + 1 < dataSize) ? rgbData[i * 6 + 1] : 255;
        uint8_t b1 = (i * 6 + 2 < dataSize) ? rgbData[i * 6 + 2] : 255;
        uint8_t r2 = (i * 6 + 3 < dataSize) ? rgbData[i * 6 + 3] : 255;
        uint8_t g2 = (i * 6 + 4 < dataSize) ? rgbData[i * 6 + 4] : 255;
        uint8_t b2 = (i * 6 + 5 < dataSize) ? rgbData[i * 6 + 5] : 255;
        
        uint8_t color1 = getClosestColor(r1, g1, b1);
        uint8_t color2 = getClosestColor(r2, g2, b2);
        
        epdData[i] = (color1 << 4) | color2;
    }
}

void DisplayHandler::drawText(uint8_t* buffer, const char* text, int x, int y, int scale) {
    // Simple 5x7 font bitmap for basic characters
    const uint8_t font5x7[][5] = {
        {0x00, 0x00, 0x00, 0x00, 0x00}, // Space
        {0x00, 0x00, 0x5F, 0x00, 0x00}, // !
        {0x00, 0x07, 0x00, 0x07, 0x00}, // "
        {0x14, 0x7F, 0x14, 0x7F, 0x14}, // #
        {0x24, 0x2A, 0x7F, 0x2A, 0x12}, // $
        {0x23, 0x13, 0x08, 0x64, 0x62}, // %
        {0x36, 0x49, 0x55, 0x22, 0x50}, // &
        {0x00, 0x05, 0x03, 0x00, 0x00}, // '
        {0x00, 0x1C, 0x22, 0x41, 0x00}, // (
        {0x00, 0x41, 0x22, 0x1C, 0x00}, // )
        {0x08, 0x2A, 0x1C, 0x2A, 0x08}, // *
        {0x08, 0x08, 0x3E, 0x08, 0x08}, // +
        {0x00, 0x50, 0x30, 0x00, 0x00}, // ,
        {0x08, 0x08, 0x08, 0x08, 0x08}, // -
        {0x00, 0x60, 0x60, 0x00, 0x00}, // .
        {0x20, 0x10, 0x08, 0x04, 0x02}, // /
        {0x3E, 0x51, 0x49, 0x45, 0x3E}, // 0
        {0x00, 0x42, 0x7F, 0x40, 0x00}, // 1
        {0x42, 0x61, 0x51, 0x49, 0x46}, // 2
        {0x21, 0x41, 0x45, 0x4B, 0x31}, // 3
        {0x18, 0x14, 0x12, 0x7F, 0x10}, // 4
        {0x27, 0x45, 0x45, 0x45, 0x39}, // 5
        {0x3C, 0x4A, 0x49, 0x49, 0x30}, // 6
        {0x01, 0x71, 0x09, 0x05, 0x03}, // 7
        {0x36, 0x49, 0x49, 0x49, 0x36}, // 8
        {0x06, 0x49, 0x49, 0x29, 0x1E}, // 9
        {0x00, 0x36, 0x36, 0x00, 0x00}, // :
        {0x00, 0x56, 0x36, 0x00, 0x00}, // ;
        {0x00, 0x08, 0x14, 0x22, 0x41}, // <
        {0x14, 0x14, 0x14, 0x14, 0x14}, // =
        {0x41, 0x22, 0x14, 0x08, 0x00}, // >
        {0x02, 0x01, 0x51, 0x09, 0x06}, // ?
        {0x32, 0x49, 0x79, 0x41, 0x3E}, // @
        {0x7E, 0x11, 0x11, 0x11, 0x7E}, // A
        {0x7F, 0x49, 0x49, 0x49, 0x36}, // B
        {0x3E, 0x41, 0x41, 0x41, 0x22}, // C
        {0x7F, 0x41, 0x41, 0x22, 0x1C}, // D
        {0x7F, 0x49, 0x49, 0x49, 0x41}, // E
        {0x7F, 0x09, 0x09, 0x01, 0x01}, // F
        {0x3E, 0x41, 0x41, 0x51, 0x32}, // G
        {0x7F, 0x08, 0x08, 0x08, 0x7F}, // H
        {0x00, 0x41, 0x7F, 0x41, 0x00}, // I
        {0x20, 0x40, 0x41, 0x3F, 0x01}, // J
        {0x7F, 0x08, 0x14, 0x22, 0x41}, // K
        {0x7F, 0x40, 0x40, 0x40, 0x40}, // L
        {0x7F, 0x02, 0x04, 0x02, 0x7F}, // M
        {0x7F, 0x04, 0x08, 0x10, 0x7F}, // N
        {0x3E, 0x41, 0x41, 0x41, 0x3E}, // O
        {0x7F, 0x09, 0x09, 0x09, 0x06}, // P
        {0x3E, 0x41, 0x51, 0x21, 0x5E}, // Q
        {0x7F, 0x09, 0x19, 0x29, 0x46}, // R
        {0x46, 0x49, 0x49, 0x49, 0x31}, // S
        {0x01, 0x01, 0x7F, 0x01, 0x01}, // T
        {0x3F, 0x40, 0x40, 0x40, 0x3F}, // U
        {0x1F, 0x20, 0x40, 0x20, 0x1F}, // V
        {0x7F, 0x20, 0x18, 0x20, 0x7F}, // W
        {0x63, 0x14, 0x08, 0x14, 0x63}, // X
        {0x03, 0x04, 0x78, 0x04, 0x03}, // Y
        {0x61, 0x51, 0x49, 0x45, 0x43}, // Z
    };
    
    int textLength = strlen(text);
    
    for (int i = 0; i < textLength; i++) {
        char c = text[i];
        int charIndex;
        
        // Convert character to font index
        if (c >= ' ' && c <= 'Z') {
            charIndex = c - ' ';
        } else {
            charIndex = 0; // Default to space for unknown characters
        }
        
        // Draw character
        for (int row = 0; row < 7; row++) {
            uint8_t fontRow = (charIndex < 91) ? font5x7[charIndex][row < 5 ? row : 4] : 0;
            
            for (int col = 0; col < 5; col++) {
                if (fontRow & (1 << col)) {
                    // Draw pixel(s) for this bit
                    for (int sy = 0; sy < scale; sy++) {
                        for (int sx = 0; sx < scale; sx++) {
                            int pixelX = x + i * 6 * scale + col * scale + sx;
                            int pixelY = y + row * scale + sy;
                            
                            if (pixelX >= 0 && pixelX < DISPLAY_WIDTH && 
                                pixelY >= 0 && pixelY < DISPLAY_HEIGHT) {
                                
                                int bufferIndex = (pixelY * 400) + (pixelX / 2);
                                
                                if (pixelX % 2 == 0) {
                                    // Left pixel (upper 4 bits) - Black
                                    buffer[bufferIndex] = (buffer[bufferIndex] & 0x0F) | (0x00);
                                } else {
                                    // Right pixel (lower 4 bits) - Black
                                    buffer[bufferIndex] = (buffer[bufferIndex] & 0xF0) | 0x00;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
