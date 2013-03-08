# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

from utils import *

class K8055Backend:
	def __init__(self, display, pinmap, board = None, port = 0):
		self.display = display
		if board:
			self.board = board
		else:
			try:
				import pyk8055
				self.board = pyk8055.k8055(port)
			except:
				raise IOError("Could not establish a connection to the K8055 board.")
		
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			if pin == 'LED':
				self.led_pwm = output > 8
	
	def high(self, output):
		self.board.SetDigitalChannel(output)
	
	def low(self, output):
		self.board.ClearDigitalChannel(output)
	
	def pulse(self, output):
		self.high(output)
		self.low(output)
	
	def all_low(self):
		self.board.ClearAllDigital()
		self.board.ClearAllAnalog()
	
	def write_nibble(self, nibble, data = True):
		mask = nibble_to_mask(nibble, data = data)
		self.board.WriteAllDigital(mask)
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			level = int(level * (255.0 / 1023.0))
			self.board.OutputAnalogChannel(self.PIN_LED - 8, level)
		else:
			if level > 0:
				self.board.SetDigitalChannel(self.PIN_LED)
			else:
				self.board.ClearDigitalChannel(self.PIN_LED)

class GPIOBackend:
	def __init__(self, display, pinmap):
		self.display = display
		try:
			import wiringpi
			self.gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
		except:
			raise IOError("Could not export the GPIO pins. Make sure that you have the wiringpi library installed, run as root and are on a Raspberry Pi.")
		
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			if pin == 'LED':
				self.led_pwm = output == 18
			self.gpio.pinMode(output, self.gpio.PWM_OUTPUT if pin == 'LED' and self.led_pwm else self.gpio.OUTPUT)
	
	def high(self, output):
		self.gpio.digitalWrite(output, True)
	
	def low(self, output):
		self.gpio.digitalWrite(output, False)
	
	def pulse(self, output):
		self.high(output)
		self.low(output)
	
	def all_low(self):
		for output in self.reverse_pinmap.keys():
			self.low(output)
	
	def write_nibble(self, nibble, data = True):
		self.gpio.digitalWrite(self.PIN_RS, data)
		self.gpio.digitalWrite(self.PIN_D4, nibble[3])
		self.gpio.digitalWrite(self.PIN_D5, nibble[2])
		self.gpio.digitalWrite(self.PIN_D6, nibble[1])
		self.gpio.digitalWrite(self.PIN_D7, nibble[0])
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			self.gpio.pwmWrite(self.PIN_LED, level)
		else:
			self.gpio.digitalWrite(self.PIN_LED, level > 0)

class ArduinoBackend:
	def __init__(self, display, pinmap, device = "/dev/ttyACM0", pwm_outputs = [3, 5, 6, 9, 10, 11]):
		self.display = display
		try:
			import serial
			self.serial = serial.serial_for_url(device, timeout = 0)
		except:
			raise IOError("Could not open the Arduino. Make sure you are running as root and are using the correct device name.")
		
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			if pin == 'LED':
				self.led_pwm = output in pwm_outputs
	
	def high(self, output):
		self.serial.write("".join(chr(b) for b in [output, 1]))
	
	def low(self, output):
		self.serial.write("".join(chr(b) for b in [output, 0]))
	
	def pulse(self, output):
		self.high(output)
		self.low(output)
	
	def all_low(self):
		for output in self.reverse_pinmap.keys():
			self.low(output)
	
	def write_nibble(self, nibble, data = True):
		self.serial.write("".join(chr(b) for b in [self.PIN_RS, int(data), self.PIN_D4, int(nibble[3]), self.PIN_D5, int(nibble[2]), self.PIN_D6, int(nibble[1]), self.PIN_D7, int(nibble[0])]))
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			level = int(level * (255.0 / 1023.0))
			self.serial.write("".join(chr(b) for b in [self.PIN_LED, level]))
		else:
			self.serial.write("".join(chr(b) for b in [self.PIN_LED, int(level > 0)]))
