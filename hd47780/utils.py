# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import sys
import termios
import tty

def bool_list_to_mask(list):
	mask = 0
	for i in range(len(list)):
		if bool(int(list[i])):
			mask += 2 ** i
	return mask

def nibble_to_mask(backend, nibble, data):
	l = [False] * 8
	l[backend.PIN_D4 - 1] = nibble[3]
	l[backend.PIN_D5 - 1] = nibble[2]
	l[backend.PIN_D6 - 1] = nibble[1]
	l[backend.PIN_D7 - 1] = nibble[0]
	if data:
		l[backend.PIN_RS - 1] = True
	mask = bool_list_to_mask(l)
	return mask

def value_to_nibbles(value):
	assert value >= 0
	assert value <= 255
	b = bin(value)[2:10]
	b = "0" * (8 - len(b)) + b
	bits = tuple([bit == "1" for bit in list(b)])
	nibbles = (bits[:4], bits[4:])
	return nibbles

class KeyReader:
	def __init__(self):
		self.buffer = []
		self.in_seq = False
		self.seq = []

	def read_key(self):
		if sys.stdin.isatty():
			fd = sys.stdin.fileno()
			old_settings = termios.tcgetattr(fd)
			try:
				tty.setraw(sys.stdin.fileno())
				char = sys.stdin.read(1)
				code = ord(char)
				if code == 3:
					raise KeyboardInterrupt
				if code == 27:
					self.in_seq = True
				if self.in_seq:
					self.seq.append(char)
					if len(self.seq) == 3:
						self.in_seq = False
						seq = self.seq[:]
						self.seq = []
						return "".join(seq)
					return
			finally:
				termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		else:
			if not self.buffer:
				self.buffer = list(sys.stdin.read())
			try:
				char = self.buffer.pop(0)
			except IndexError:
				raise SystemExit
		return char
