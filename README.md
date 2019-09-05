# Exo Sense Py Modbus
Modbus RTU Slave and Modbus TCP Server app for Exo Sense Py, configurable via FTP or Web server.

## Installation
Just copy all the files in this repo into the Pycom's flash memory.

## User guide
Power on Exo Sense Py, the internal LED light will turn on as fixed red. Wait for the LED to turn blue or green.

If green, the module is already configured and ready to process Modbus requests. On the first Modbus request received the LED will go off.

If blue, the module is not configured and is set to access point mode. After some time (see below) the access point will be automatically disabled.

### Configuration

All configuration parameters are in the [config.py](config.py) file.

To access this file on the module, enable access point mode and join its WiFi network. Depending on the configuration, a Web server and/or an FTP server will be enabled. Using any Web browser or FTP client application, connect to 192.168.4.1 using the credentials specified in the configuration.

Refer to [config.py](config.py) for the default WiFi, Web and FTP credentials.

Download the configuration file, edit it and re-upload it. If using the Web interface, after the upload, Exo will automatically restart using the new configuration, otherwise, on the next power-on, it will start with the new configuration.

Configure it to work as Modbus RTU slave __or__ Modbus TCP server, by setting `MB_RTU_ADDRESS` __or__ `MB_TCP_IP` to a valid value. If both are set, the TCP configuration will be ignored. If neither are, it will boot as _not configured_ and enable the access point at power-on.

When configured as Modbus TCP server, the configuration Web interface and/or FTP server will be available at the configured IP address. If Exo cannot connect to the specified WiFi, after the time specified by the `AP_ON_TIMEOUT_SEC` configuration parameter, it will go into access point mode.

When configured as RTU slave, to re-enable access point mode, write register 5 via Modbus (see below), or power on the module and wait without making any Modbus requests for the time specified by the `AP_ON_TIMEOUT_SEC` parameter.

The above access point mode auto-enable routine can be disabled by setting `AP_ON_TIMEOUT_SEC` to `0`.

The access point is automatically disabled after the time specified by `AP_ON_TIME_SEC`.

### LED status table

|LED status|Description|
|:--------:|-----------|
|Red|Starting up|
|Green|Ready and waiting for first Modbus request|
|Off or Blue blink|Running (`HEARTBEAT_LED` config option)|
|Blue|Access point on|
|Yellow|Enabling access point|
|Purple blink|Connecting to WiFi (TCP mode)|
|Red blink|Not configured and AP timeout expired, reboot to re-enable access point|

## Modbus registers

Refer to the following table for the list of available registers and corresponding supported Modbus functions.

For the "Functions" column:    
1 = Read coils    
2 = Read discrete inputs    
3 = Read holding registers    
4 = Read input registers    
5 = Write single coil    
6 = Write single register    
15 = Write multiple coils    
16 = Write multiple registers    

|Address|R/W|Functions|Size (bits)|Data type|Unit|Description|
|------:|:-:|---------|----|---------|----|-----------|
|5|W|5|1|-|-|Write ON (0xFF00) to enable access point mode (RTU only)|
|101|R|2|1|-|-|Digital input DI1|
|102|R|2|1|-|-|Digital input DI2|
|201|R/W|1,5|1|-|-|Digital output DO1|
|211|W|6|16|unsigned short|ms|DO1 pulse|
|301|R|4|16|signed short|&deg;C/10|Temperature|
|302|R|4|16|unsigned short|&permil;|Relative humidity|
|303|R|4|16|unsigned short|hPa/10|Atmospheric pressure|
|304|R|4|16|unsigned short|K&#8486;|Air resistance (quality indication)|
|305|R|4|16|unsigned short|lx/10|Light intensity|
|306|R|4|16|unsigned short|-|Noise intensity|
|307|R|4|16|unsigned short|-|Peak programme meter simulation on noise value|
|308|R|4|16|unsigned short|-|IAQ index (see [below](#iaq-index))|
|309|R|4|16|signed short|-|IAQ trend: a positive value represents an IAQ improvement, a negative value an IAQ worsening, a value of zero represents a stable IAQ|
|401|W|6|16|unsigned short|ms|Buzzer beep|

### IAQ index

IAQ (Indoor Air Quality) index description:

|IAQ index|Air Quality|
|:-------:|:---------:|
|0-50|Good|
|51-100|Average|
|101-150|Little bad|
|151-200|Bad|
|201-300|Worse|
|301-500|Very bad|
