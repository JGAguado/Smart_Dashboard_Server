#include <Arduino.h>
#include <WiFi.h>
#include <SPI.h>
#include <Update.h>
#include "serial_config.h"  // Must be included first
#include "config.h"
#include "config_manager.h"
#include "display_handler.h"
#include "web_server.h"
#include "github_fetcher.h"
#include "utils.h"

// Global objects
ConfigManager configManager;
DisplayHandler display;
WebConfigServer webServer(&configManager);
GitHubImageFetcher imageFetcher(&configManager);

// State variables
bool isConfigMode = false;
unsigned long lastUpdateTime = 0;
unsigned long lastWiFiCheck = 0;
bool firstRun = true;

// Function declarations
void setup();
void loop();
bool connectToWiFi();
void enterConfigMode();
void exitConfigMode();
void updateDashboard();
void checkWiFiConnection();
void printSystemInfo();

void setup() {
    initSerial();  // Initialize hardware UART
    delay(1000);
    
    Serial.println("\n" + repeat("=", 50));
    Serial.println("ESP32-S2 Smart Dashboard Starting...");
    Serial.println("Version: 1.0.0");
    Serial.println("Display: 7.3\" 7-color E-Paper (800x480)");
    Serial.println(repeat("=", 50));
    
    // Initialize EEPROM and configuration
    Serial.println("Initializing configuration manager...");
    if (!configManager.init()) {
        Serial.println("Failed to initialize configuration manager");
    }
    
    // Initialize display
    Serial.println("Initializing display...");
    if (!display.initialize()) {
        Serial.println("WARNING: Display initialization failed!");
        Serial.println("Continuing without display...");
    }
    
    // Check if device is configured
    if (!configManager.isConfigured()) {
        Serial.println("No saved configuration found");
        
        // Try to load default configuration
        Serial.println("Attempting to load default configuration...");
        if (configManager.loadDefaultConfig()) {
            Serial.println("Default configuration loaded successfully!");
            // Continue to WiFi connection attempt below
        } else {
            Serial.println("No default configuration available - entering configuration mode");
            display.showStatus("Configuration Mode");  // This will show the QR code
            enterConfigMode();
            printSystemInfo();
            Serial.println("Setup complete - in configuration mode!");
            return; // Exit setup early when in config mode
        }
    } else {
        Serial.println("Saved configuration found");
        configManager.printConfig();
    }
    
    // At this point we have configuration (either saved or default)
    Serial.println("Configuration available - attempting to connect to WiFi");
    
    if (connectToWiFi()) {
        Serial.println("Connected to WiFi - starting normal operation");
        // Don't display anything - wait for image fetch
        lastUpdateTime = 0; // Force immediate update
    } else {
        Serial.println("Failed to connect to WiFi - entering configuration mode");
        // Only show display for configuration mode
        display.showStatus("Configuration Mode");
        enterConfigMode();
    }
    
    printSystemInfo();
    Serial.println("Setup complete!");
}

void loop() {
    if (isConfigMode) {
        // Handle configuration mode
        webServer.handleClient();
        delay(100);
    } else {
        // Normal operation mode
        checkWiFiConnection();
        
        // Check if it's time to update the dashboard
        unsigned long currentTime = millis();
        if (firstRun || (currentTime - lastUpdateTime >= UPDATE_INTERVAL_MS)) {
            updateDashboard();
            lastUpdateTime = currentTime;
            firstRun = false;
        }
        
        // Sleep for a while to save power
        delay(30000); // Check every 30 seconds
    }
}

bool connectToWiFi() {
    if (!configManager.isConfigured()) {
        Serial.println("Cannot connect to WiFi: no configuration");
        return false;
    }
    
    const char* ssid = configManager.getWiFiSSID();
    const char* password = configManager.getWiFiPassword();
    
    Serial.printf("Connecting to WiFi: %s\n", ssid);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    const int maxAttempts = 30; // 30 seconds timeout
    
    while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts) {
        delay(1000);
        attempts++;
        Serial.printf("WiFi connection attempt %d/%d\n", attempts, maxAttempts);
        
        // Don't show progress on display - keep it blank
        if (attempts % 5 == 0) {
            // Just log progress, don't display anything
            Serial.printf("WiFi connection progress: %d/%d attempts\n", attempts, maxAttempts);
        }
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("WiFi connected successfully!");
        Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
        return true;
    } else {
        Serial.println("WiFi connection failed");
        return false;
    }
}

void enterConfigMode() {
    Serial.println("Entering configuration mode...");
    isConfigMode = true;
    
    if (!webServer.startConfigAP()) {
        Serial.println("Failed to start configuration server");
        display.showStatus("Config Server Failed");
        return;
    }
    
    // Show QR code for easy WiFi connection
    display.showStatus("Configuration Mode");
    
    Serial.println("Configuration mode active - waiting for user input");
}

void exitConfigMode() {
    Serial.println("Exiting configuration mode...");
    isConfigMode = false;
    webServer.stopServer();
}

void updateDashboard() {
    Serial.println("\n" + repeat("-", 40));
    Serial.println("Starting dashboard update...");
    
    // Don't display anything during fetch - keep display blank
    
    // Test GitHub connection first
    if (!imageFetcher.testConnection()) {
        Serial.println("GitHub connection test failed");
        // Don't display error - just log it
        return;
    }
    
    // Fetch the latest image
    if (imageFetcher.fetchLatestImage()) {
        Serial.println("Image fetched successfully");
        
        uint8_t* imageData = imageFetcher.getImageBuffer();
        size_t imageSize = imageFetcher.getImageSize();
        
        Serial.printf("Displaying image (%d bytes)\n", imageSize);
        // This is the ONLY display call - show the fetched image
        display.displayImage(imageData, imageSize);
        
        Serial.println("Dashboard update completed successfully");
    } else {
        Serial.println("Failed to fetch image from GitHub");
        // Don't display error - just log it and keep display blank
    }
    
    Serial.println(repeat("-", 40));
}

void checkWiFiConnection() {
    unsigned long currentTime = millis();
    
    // Check WiFi every 30 seconds
    if (currentTime - lastWiFiCheck >= WIFI_RETRY_DELAY_MS) {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("WiFi disconnected - attempting to reconnect");
            
            if (!connectToWiFi()) {
                Serial.println("WiFi reconnection failed - entering configuration mode");
                display.showStatus("WiFi Lost - Config Mode");
                delay(3000);
                enterConfigMode();
            }
        }
        lastWiFiCheck = currentTime;
    }
}

void printSystemInfo() {
    Serial.println("\n" + repeat("=", 50));
    Serial.println("SYSTEM INFORMATION");
    Serial.println(repeat("=", 50));
    Serial.printf("Chip Model: %s\n", ESP.getChipModel());
    Serial.printf("Chip Revision: %d\n", ESP.getChipRevision());
    Serial.printf("CPU Frequency: %d MHz\n", ESP.getCpuFreqMHz());
    Serial.printf("Flash Size: %d KB\n", ESP.getFlashChipSize() / 1024);
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("PSRAM Size: %d KB\n", ESP.getPsramSize() / 1024);
    Serial.printf("Free PSRAM: %d bytes\n", ESP.getFreePsram());
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("WiFi SSID: %s\n", WiFi.SSID().c_str());
        Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("MAC Address: %s\n", WiFi.macAddress().c_str());
        Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
    }
    
    Serial.printf("Configuration Status: %s\n", configManager.isConfigured() ? "Configured" : "Not Configured");
    Serial.printf("Display Status: Initialized");
    Serial.printf("Operating Mode: %s\n", isConfigMode ? "Configuration" : "Normal");
    Serial.println(repeat("=", 50));
}