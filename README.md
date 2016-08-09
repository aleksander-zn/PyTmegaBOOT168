# PyTmegaBOOT168
An implementation of ATmegaBOOT_168 (bootloader that comes with Arduino IDE and is burned on Arduino Nanos) in Python. Useful for debugging.

## Usage example
```
socat pty,raw,echo=0,link=/tmp/ttyV0 pty,raw,echo=0,link=/tmp/ttyV1 &
./PyTmegaBOOT168.py /tmp/ttyV0 57600 > PyTmega.out &
avrdude -p m328p -b 57600 -c arduino -P /tmp/ttyV1
```
