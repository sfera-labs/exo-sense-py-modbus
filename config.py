# Access point WiFi name (SSID)
AP_SSID = 'ExoSensePy'

# Access point WiFi password
AP_PASSWORD = 'exosense'

# Access point WiFi channel
AP_CHANNEL = 7

# Duration of access point mode, is seconds.
# Values below 120 (2 mins) are ignored.
AP_ON_TIME_SEC = 600

# Time (seconds) after power-on after which access point mode is enabled
# if the module is configured and no Modbus RTU request is received or
# if cannot connect to WiFi (Modbus TCP).
# Set to 0 to disable access point mode.
AP_ON_TIMEOUT_SEC = 300

# Web server credentials
WEB_USER = 'exo'
WEB_PASSWORD = 'sense'

# FTP server credentials
FTP_USER = 'exo' # Set to '' to disable FTP server
FTP_PASSWORD = 'sense'

# LED status when working normally
HEARTBEAT_LED = False # LED off
# HEARTBEAT_LED = True # LED short blue blink on every Modbus request

# Temperature offset (°C)
TEMP_OFFSET = 0

# Elevation from sea level in meters, for atmospheric pressure calculation
ELEVATION = 103


# Modbus RTU parameters

MB_RTU_ADDRESS = 0 # Set to 0 to disable
MB_RTU_BAUDRATE = 19200
MB_RTU_DATA_BITS = 8
MB_RTU_STOP_BITS = 1
MB_RTU_PARITY = 1 # 1 = even, 2 = odd, 3 = none


# Modbus TCP parameters

MB_TCP_IP = '' # Modbus TCP disabled
#MB_TCP_IP = 'dhcp' # Use DHCP to obtain IP address
#MB_TCP_IP = '192.168.1.100' # Static IP address

MB_TCP_MASK = '255.255.255.0' # Network mask
MB_TCP_GW = '192.168.1.1' # Gateway IP address
MB_TCP_DNS = '192.168.1.1' # DNS IP address

MB_TCP_PORT = 502 # Port for Modbus TCP requests

MB_TCP_WIFI_SSID = 'MyWiFi' # SSID of the WiFi network to connect to
MB_TCP_WIFI_PWD = 's3cretP4ssw0rd' # WiFi password
MB_TCP_WIFI_SEC = 3 # WiFi security: 0 = Open, 1 = WEP, 2 = WPA, 3 = WPA2
