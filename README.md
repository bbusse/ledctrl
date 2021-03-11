# ledctrl

A daemon and client to control LEDs or  
LED "displays"  
  
It is currently primarily used to send frames  
to a ESP8266 board with a firmware that takes  
colours encoded in hex via UDP to control WS2812b  
RGB LEDs.  
  
The firmware for the ESP8266 can be found here:  
git://git.stuge.se/esp8266-ws2812b.git  

On the first invocation of ledctrl the process  
respawns itself as a transient systemd service  
and starts sending frames to the configured IP  
by executing the configured default action.  
  
Any following invocation will trigger the client  
mode and can be used to change the currently  
active action by sending commands to the server  
process.  
  
Use 'ledctrl help' to get a usage overview.

## Dependencies

Python3
python-systemd
