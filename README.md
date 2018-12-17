# Exo Sense Py Modbus RTU
Modbus RTU Slave app for Exo Sense Py.

## Installation
Just copy all the files in this repo into the Pycom's flash memory.

## User guide
Power on Exo Sense Py, the internal LED light will turn on as fixed red. Wait for the LED to turn blue or green.

If green, the module is already configured with a Modbus address and is ready to process Modbus requests. On the first Modbus request received the LED will go off.

If blue, the module is not configured and is set to access point mode. After some time (see below) the access point will be automatically disabled.

### Configuration

All configuration parameters are in the [config.py](config.py) file.

To access this file on the module, enable access point mode and join its WiFi network. Using any FTP client application, connect to 192.168.4.1 using the credentials specified in the configuration.

Refer to [config.py](config.py) for the default WiFi and FTP credentials.

Download the file, edit it and re-upload it. On the next power-on it will start with the new configuration.

To re-enable access point mode when the module is already configured, write register 5 via Modbus (see below), or power on the module and wait without making any Modbus requests for the time specified by the `AP_ON_MB_TIMEOUT_SEC` parameter in the configuration.

The auto-enable on Modbus timeout can be disabled by setting `AP_ON_MB_TIMEOUT_SEC` to `0`.

If `MB_ADDRESS` is set to `0`, Exo Sense will boot as _not configured_ and enable the access point at power-on.

The access point is automatically disabled after the time specified by `AP_ON_TIME_SEC`.

### LED status table

|LED status|Description|
|:--------:|-----------|
|Red|Starting up|
|Green|Ready and waiting for first Modbus request|
|Off|Running|
|Blue|Access point on|
|Yellow|Enabling access point|
|Red blink|Not configured, reboot to enable access point|
|Blue blink|Boot error|

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
|5|W|5|1|-|-|Write ON (0xFF00) to enable access point mode|
|101|R|2|1|-|-|Digital input DI1|
|102|R|2|1|-|-|Digital input DI2|
|201|R/W|1,5|1|-|-|Digital output DO1|
|211|W|6|16|unsigned short|ms|DO1 pulse|
|301|R|4|16|signed short|&deg;C/10|Temperature|
|401|R|4|16|unsigned short|&permil;|Relative humidity|
|501|R|4|16|unsigned short|hPa/10|Pressure|
|601|R|4|16|unsigned short|K&#8486;|Air resistance|
|701|R|4|16|unsigned short|lx/10|Light intensity|
|801|R|4|16|unsigned short|-|Noise intensity|
|802|R|4|16|unsigned short|-|Peak programme meter simulation on noise value|
|901|W|6|16|unsigned short|ms|Buzzer beep|
