# -*- coding: utf-8 -*-
#!/usr/bin/python
#
# Measure object and ambient temperature using TN9 sensor
#
# Author : Edoardo Raparelli
# Date   : 2019/11/11
# -----------------------

import wiringpi as wp

class TN9():

    __IRTEMP_DATA_SIZE = 5
    __IRTEMP_TIMEOUT = 2000  # milliseconds
    # Each 5-byte data packet from the IRTemp is tagged with one of these
    __IRTEMP_DATA_AMBIENT = 0x66
    __IRTEMP_DATA_IR =      0x4C
    #__IRTEMP_DATA_JUNK =    0x53; # ignored, contains version info perhaps?

    def __init__(self, pinAcquire, pinClock, pinData, scale):
        self.__pinAcquire = pinAcquire
        self.__pinClock =   pinClock
        self.__pinData =    pinData
        self.__scale =      scale

        # One of the following MUST be called before using IO functions:
        #wp.wiringPiSetup()      # For sequential pin numbering
        # OR
        #wp.wiringPiSetupSys()   # For /sys/class/gpio with GPIO pin numbering
        # OR
        wp.wiringPiSetupGpio()  # For GPIO pin numbering

        if self.__pinAcquire != -1:
            wp.pinMode(self.__pinAcquire, 1)
            wp.digitalWrite(self.__pinAcquire, 1)

        wp.pinMode(self.__pinClock,   0)
        wp.pinMode(self.__pinData,    0)

        wp.digitalWrite(self.__pinClock,   1)
        wp.digitalWrite(self.__pinData,    1)

        self.__sensorEnable(False)

    def getAmbientTemperature(self):
        return self.__getTemperature(self.__IRTEMP_DATA_AMBIENT)

    def getIRTemperature(self):
        return self.__getTemperature(self.__IRTEMP_DATA_IR)

    def __getTemperature(self, dataType):
        timeout = wp.millis() + self.__IRTEMP_TIMEOUT
        self.__sensorEnable(True)

        while True:
            data = [0] * self.__IRTEMP_DATA_SIZE
            for data_byte in range(0, self.__IRTEMP_DATA_SIZE, 1):
                for data_bit in range(7, -1, -1):
                    # Clock idles high, data changes on falling edge, sample on rising edge
                    while wp.digitalRead(self.__pinClock) == 1 and wp.millis() < timeout:
                        pass # Wait for falling edge
                    while wp.digitalRead(self.__pinClock) == 0 and wp.millis() < timeout:
                        pass # Wait for rising edge to sample
                    if wp.digitalRead(self.__pinData):
                        data[data_byte] |= 1 << data_bit
            if wp.millis() >= timeout:
                self.__sensorEnable(False)
                return float('nan')

            if data[0] == dataType and self.__validData(data):
                self.__sensorEnable(False)
                temperature = self.__decodeTemperature(data);
                if self.__scale == "FAHRENHEIT":
                    temperature = self.__convertFahrenheit(temperature)
                return temperature

    def __convertFahrenheit(self, celsius):
        return celsius * 9 / 5 + 32

    def __decodeTemperature(self, data):
        msb = data[1] << 8
        lsb = data[2]
        return (msb + lsb) / 16.0 - 273.15

    def __sensorEnable(self, state):
        if self.__pinAcquire != -1:
            wp.digitalWrite(self.__pinAcquire, not state)

    def __validData(self, data):
        checksum = (data[0] + data[1] + data[2]) & 0xff
        return data[3] == checksum  and  data[4] == 0x0d


if __name__ == "__main__":

    from time import sleep

    PIN_DATA    = 17 # Choose any pins you like for these
    PIN_CLOCK   = 27
    PIN_ACQUIRE = 22
    SCALE="CELSIUS" # Options are CELSIUS, FAHRENHEIT

    SCALE_UNITS = {"CELSIUS" : "°C",
                   "FAHRENHEIT" : "°F"}

    tn9 = TN9(PIN_ACQUIRE, PIN_CLOCK, PIN_DATA, SCALE)

    while True:
        irTemperature = tn9.getIRTemperature()
        ambientTemperature = tn9.getAmbientTemperature()
        print("Object temperature = %.1f %s, Ambient temperature = %.1f %s" % (irTemperature, SCALE_UNITS[SCALE], ambientTemperature, SCALE_UNITS[SCALE]))
        sleep(2)
