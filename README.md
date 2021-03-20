# ledctrl

A HomeKit enabled daemon and client to control LEDs or LED "displays"  
  
It is currently primarily used to send frames to a ESP8266 board with a firmware that takes
colours encoded in hex via UDP to control WS2812b RGB LEDs.  
  
The firmware for the ESP8266 can be found here:  
git://git.stuge.se/esp8266-ws2812b.git  

On the first invocation of ledctrl the process respawns itself as a transient systemd user service and starts sending frames to the configured IP
by executing the configured default action.  
  
Any following invocation will trigger the client mode and can be used to change the currently active action by sending commands to the server process.

## Usage
Install required Python moduled
```
$ pip install --user -r requirements.txt
```
Use 'ledctrl help' to get a usage overview.
```
$ ledctrl help
```
It is recommended to set the required variables via the ENVIRONMENT,
e.g. by adding them to shellrc
```
$ LEDCTRL_ADDRESS=10.23.42.64 \
  LEDCTRL_PORT=4223 \
  LEDCTRL_TARGET_0_ADDRESS=10.23.42.110 \
  LEDCTRL_TARGET_0_PORT=2342 \
  LEDCTRL_TARGET_0_DIM_X=32 \
  LEDCTRL_TARGET_0_DIM_Y=24 \
  ledctrl turn-on
```
Alternatively via command line arguments
```
$ ledctrl --address=10.23.42.64 \
          --port=4223 \
          --target_address=10.23.64.110 \
          --target_port=2342 \
          --target_dim_x=32 \
          --target_dim_y=24 \
          turn-on
```
## Debug
Use the '--debug' switch or set LEDCTRL_DEBUG=True in the ENVIRONMENT  
  
Watch the Journal output
```
$ journalctl --user -afn100 -uledctrl
```
For the HomeKit part
```
$ journalctl --user -afn100 -uledctrl-homekit
```

## Dependencies
- Python3
- python-systemd
- homekit_python
