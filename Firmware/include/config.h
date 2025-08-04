#ifndef CONFIG_H
#define CONFIG_H

// E-Paper Display GPIO Configuration
// 7.3" 7-color e-paper display connections
#define EPD_BUSY_PIN    5   // GPIO5 - Busy signal from display
#define EPD_RST_PIN     6   // GPIO6 - Reset pin
#define EPD_DC_PIN      7   // GPIO7 - Data/Command selection
#define EPD_CS_PIN      8   // GPIO8 - Chip Select (SPI)
#define EPD_DIN_PIN     35  // GPIO35 - SPI MOSI (Data In)
#define EPD_SCK_PIN     36  // GPIO36 - SPI Clock

// Display specifications
#define DISPLAY_WIDTH   800
#define DISPLAY_HEIGHT  480

// Network Configuration
#define AP_SSID         "SmartDashboard-Setup"
#define AP_PASSWORD     "configure123"
#define CONFIG_TIMEOUT  300000  // 5 minutes timeout for configuration

// Web server configuration
#define WEB_SERVER_PORT 80
#define DNS_PORT        53

// GitHub Configuration
#define GITHUB_HOST     "raw.githubusercontent.com"
#define GITHUB_PORT     443
#define MAX_IMAGE_SIZE  200000  // 200KB max image size

// Update intervals
#define UPDATE_INTERVAL_MS      3600000  // 1 hour in milliseconds
#define WIFI_RETRY_DELAY_MS     30000    // 30 seconds between WiFi retries
#define CONFIG_CHECK_INTERVAL   5000     // Check for configuration every 5 seconds

// EEPROM Configuration addresses
#define EEPROM_SIZE             512
#define EEPROM_WIFI_SSID_ADDR   0
#define EEPROM_WIFI_PASS_ADDR   64
#define EEPROM_GITHUB_REPO_ADDR 128
#define EEPROM_GITHUB_PATH_ADDR 192
#define EEPROM_CONFIG_FLAG_ADDR 256

// Configuration validation
#define CONFIG_MAGIC_NUMBER     0xABCD
#define MAX_SSID_LENGTH         63
#define MAX_PASSWORD_LENGTH     63
#define MAX_REPO_LENGTH         63
#define MAX_PATH_LENGTH         63

#endif // CONFIG_H
