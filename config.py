# Access point WiFi name (SSID)
AP_SSID = 'Exo_AP'

# Access point WiFi password
AP_PASSWORD = 'exosense'

# Access point WiFi channel
AP_CHANNEL = 7

# DUration of access point mode, is seconds.
# Values below 120 (2 mins) are ignored.
AP_ON_TIME_SEC = 600

# Time (seconds) after power-on after which access point mode is enabled
# if the module is configured and no Modbus request is received.
# Set to 0 to disable.
AP_ON_MB_TIMEOUT_SEC = 300

# FTP server credentials
FTP_USER = 'exo'
FTP_PASSWORD = 'sense'

# Modbus parameters
MB_ADDRESS = 10 # Set to 0 to boot as not configured (AP on)
MB_BAUDRATE = 19200
MB_DATA_BITS = 8
MB_STOP_BITS = 1
MB_PARITY = 1 # 1 = even, 2 = odd, 3 = none

# Temperature offset (°C)
TEMP_OFFSET = 0
