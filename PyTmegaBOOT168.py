#!/usr/bin/env python3
import serial
import sys

def hex_ascii(c):
	r = format(c, '#04x')
	if c < 0x80 and chr(c).isprintable(): r += ' (' + chr(c) + ')'
	return r

def getch(s):
	c = s.read()[0]
	print('getch(): ' + hex_ascii(c))
	return c

def getNch(s, count):
	for _ in range(count): getch(s)

def putch(s, c):
	print('putch(): ' + hex_ascii(c))
	s.write(bytes([c]))

def nothing_response(s):
	if getch(s) == ord(' '):
		putch(s, 0x14)
		putch(s, 0x10)

def byte_response(s, b):
	if getch(s) == ord(' '):
		putch(s, 0x14)
		putch(s, b)
		putch(s, 0x10)

# op should be either 'read' or 'write'
def rw_msg(op, len, addr, eeprom):
	prep = 'from' if (op == 'read') else 'into'
	mem = 'eeprom' if eeprom else 'flash'
	return (op + ' page of ' + format(len, '#06x') + ' bytes @ ' +
		format(addr, '#08x') + ' ' + prep + ' ' + mem)

def usage():
	print('usage: ' + sys.argv[0] + ' <tty-or-pts-dev-file> [<baud-rate>]')
	print('e.g.:  ' + sys.argv[0] + ' /dev/ttyS0')
	print('       ' + sys.argv[0] + ' /dev/pts/0 9600')

HW_VER = 0x02
SW_MAJOR = 0x01
SW_MINOR = 0x10
SIG1 = 0x1e
SIG2 = 0x95
SIG3 = 0x0f

def main_loop(ser):
	address = 0

	done = False
	while not done:
		ch = getch(ser)

		if ch == ord('0'):
			print('get synchronization')
			nothing_response(ser)

		# is seems that avrdude doesn't ever use this command regardless
		# of the programmer in use (stk500v1/arduino)
		elif ch == ord('1'):
			if getch(ser) == ord(' '):
				print('check if starterkit present')
				putch(ser, 0x14)
				putch(ser, ord('A'))
				putch(ser, ord('V'))
				putch(ser, ord('R'))
				putch(ser, ord(' '))
				putch(ser, ord('I'))
				putch(ser, ord('S'))
				putch(ser, ord('P'))
				putch(ser, 0x10)

		elif ch == ord('A'):
			print('get parameter value')
			ch2 = getch(ser)
			if ch2 == 0x80: byte_response(ser, HW_VER)
			elif ch2 == 0x81: byte_response(ser, SW_MAJOR)
			elif ch2 == 0x82: byte_response(ser, SW_MINOR)
			elif ch2 == 0x98: byte_response(ser, 0x03)
			else: byte_response(ser, 0x00)

		elif ch == ord('B'):
			print('set device programming parameters')
			getNch(ser, 20)
			nothing_response(ser)

		elif ch == ord('E'):
			print('set extended device programming parameters')
			getNch(ser, 5)
			nothing_response(ser)

		elif ch == ord('P'):
			print('enter program mode')
			nothing_response(ser)

		elif ch == ord('u'):
			print('read signature bytes')
			if getch(ser) == ord(' '):
				putch(ser, 0x14)
				putch(ser, SIG1)
				putch(ser, SIG2)
				putch(ser, SIG3)
				putch(ser, 0x10)

		elif ch == ord('V'):
			print('universal command')
			if getch(ser) == 0x30:
				getch(ser)
				ch = getch(ser)
				getch(ser)
				if ch == 0: byte_response(ser, SIG1)
				elif ch == 1: byte_response(ser, SIG2)
				else: byte_response(ser, SIG3)
			else:
				getNch(ser, 3)
				byte_response(ser, 0x00)

		elif ch == ord('U'):
			# little-endian, word address
			address = getch(ser)
			address += getch(ser) << 8
			# convert word address to byte address
			address *= 2
			print('load address: ' + format(address, '#08x') +
			      ' (byte address)')
			nothing_response(ser)

		elif ch == ord('t'):
			# big-endian, in bytes
			length = getch(ser) << 8
			length += getch(ser)
			if getch(ser) == ord('E'): eeprom = True
			else: eeprom = False
			if getch(ser) == ord(' '):
				print(rw_msg('read', length, address, eeprom))
				putch(ser, 0x14)
				for _ in range(length): putch(ser, 0xff)
				putch(ser, 0x10)

		elif ch == ord('d'):
			# big-endian, in bytes
			length = getch(ser) << 8
			length += getch(ser)
			if getch(ser) == ord('E'): eeprom = True
			else: eeprom = False
			for _ in range(length): getch(ser)
			if getch(ser) == ord(' '):
				print(rw_msg('write', length, address, eeprom))
				putch(ser, 0x14)
				putch(ser, 0x10)

		elif ch == ord('Q'):
			print('leave program mode')
			nothing_response(ser)
			done = True

def main():
	argc = len(sys.argv)
	if argc < 2:
		usage()
		sys.exit(0)

	baud = 57600
	if argc >= 3:
		try: baud = int(sys.argv[2])
		except ValueError as e:
			print(repr(e))
			usage()
			sys.exit(1)

	ser = serial.Serial(sys.argv[1], baud)

	try: main_loop(ser)
	except KeyboardInterrupt: pass

	ser.close()

if __name__ == '__main__': main()
