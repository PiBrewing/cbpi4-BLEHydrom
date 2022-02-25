
# -*- coding: utf-8 -*-
from multiprocessing import Process, Manager
import time
import os
from aiohttp import web
import logging
from unittest.mock import MagicMock, patch
import asyncio
import random
from cbpi.api import *
import bluetooth._bluetooth as bluez
from . import blescan
#from bleak import BleakScanner

logger = logging.getLogger(__name__)

import numpy as np

global tilt_cache

tilt_proc = None
tilt_manager = None
tilt_cache = {}
cache = {}

TILTS = {
	'a495bb10c5b14b44b5121370f02d74de': 'Red',
	'a495bb20c5b14b44b5121370f02d74de': 'Green',
	'a495bb30c5b14b44b5121370f02d74de': 'Black',
	'a495bb40c5b14b44b5121370f02d74de': 'Purple',
	'a495bb50c5b14b44b5121370f02d74de': 'Orange',
	'a495bb60c5b14b44b5121370f02d74de': 'Blue',
	'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
	'a495bb80c5b14b44b5121370f02d74de': 'Pink',
}

def add_calibration_point(x, y, field):
    if isinstance(field, str) and field:
        x1, y1 = field.split("=")
        x = np.append(x, float(x1))
        y = np.append(y, float(y1))
    return x, y

def calcGravity(gravity, unitsGravity):
    sg = float(gravity)/1000
    #logging.info(sg)
    #logging.info(unitsGravity)
    if (unitsGravity == "Plato"):
        # Source: https://en.wikipedia.org/wiki/Brix
        return ((135.997 * sg - 630.272) * sg + 1111.14) * sg - 616.868
    elif (unitsGravity == "Brix"):
        # Source: https://en.wikipedia.org/wiki/Brix
        return ((182.4601 * sg - 775.6821) * sg + 1262.7794) * sg - 669.5622
    else:
        return sg

def calcTemp(temp,unit):
	f = float(temp)
	if unit == "C":
		return (f - 32) / 1.8
	else:
		return f

def calibrate(tilt, equation):
    return eval(equation)
	
def distinct(objects):
    seen = set()
    unique = []
    for obj in objects:
        if obj['uuid'] not in seen:
            unique.append(obj)
            seen.add(obj['uuid'])
    return unique

def readTilt(cache):
    dev_id = 0
    while True:
        try:
            logging.info("Starting Bluetooth connection")
            sock = bluez.hci_open_dev(dev_id)
            blescan.hci_le_set_scan_parameters(sock)
            blescan.hci_enable_le_scan(sock)

            while True:
                beacons = distinct(blescan.parse_events(sock, 10))
                #print(beacons)
                for beacon in beacons:
                    if beacon['uuid'] in TILTS.keys():
                        cache[TILTS[beacon['uuid']]] = {'Temp': beacon['major'], 'Gravity': beacon['minor'], 'Time': time.time(),'RSSI': beacon['rssi']}
                        #logging.info(cache)
                        logging.info("Tilt data received: Temp: %s Gravity: %s RSSI: %s" % (beacon['major'], beacon['minor'], beacon['rssi']))
                        time.sleep(4)
        except Exception as e:
            logging.error("Error starting Bluetooth device, exception: %s" % str(e))

        logging.info("Restarting Bluetooth process in 10 seconds")
        time.sleep(10)



@parameters([Property.Select(label="Sensor color", options=["Red", "Green", "Black", "Purple", "Orange", "Blue", "Yellow", "Pink"], description="Select the color of your Tilt"),
	         Property.Select(label= "Data Type", options=["Temperature", "Gravity","RSSI"], description="Select which type of data to register for this sensor"),
	         Property.Select(label="Gravity Units", options=["SG", "Brix", "Plato"], description="Converts the gravity reading to this unit if the Data Type is set to Gravity"),
	         Property.Text(label="Calibration Point 1", configurable=True, default_value="", description="Optional field for calibrating your Tilt. Enter data in the format uncalibrated=actual"),
             Property.Text(label="Calibration Point 2", configurable=True, default_value="", description="Optional field for calibrating your Tilt. Enter data in the format uncalibrated=actual"),
             Property.Text(label="Calibration Point 3", configurable=True, default_value="", description="Optional field for calibrating your Tilt. Enter data in the format uncalibrated=actual")])
class BLESensor(CBPiSensor):
    
    def __init__(self, cbpi, id, props):
        super(BLESensor, self).__init__(cbpi, id, props)
        global titl_cache
        self.value = 0
        self.calibration_equ=""
        self.x_cal_1=self.props.get("Calibration Point 1","")
        self.x_cal_2=self.props.get("Calibration Point 2","")
        self.x_cal_3=self.props.get("Calibration Point 3","")

        self.color=self.props.get("Sensor color","")
        self.sensorType=self.props.get("Data Type","Temperature")
        self.unitsGravity=self.props.get("Gravity Units","Plato")
        self.time_old = float(0)
        # Load calibration data from plugin
        x = np.empty([0])
        y = np.empty([0])
        x, y = add_calibration_point(x, y, self.x_cal_1)
        x, y = add_calibration_point(x, y, self.x_cal_2)
        x, y = add_calibration_point(x, y, self.x_cal_3)

        # Create calibration equation
        if len(x) < 1:
            self.calibration_equ = "tilt"
        if len(x) == 1:
            self.calibration_equ = 'tilt + {0}'.format(y[0] - x[0])
        if len(x) > 1:
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            self.calibration_equ = '{0}*tilt + {1}'.format(m, c)

        #logging.info('Calibration equation: {0}'.format(self.calibration_equ))

    async def run(self):
        while self.running is True:
            if self.color in tilt_cache:
                current_time = float(tilt_cache[self.color]['Time'])
                #logging.info("Color: {} | Time Old: {} | Curent Time: {}".format(self.color,self.time_old,current_time))
                if self.sensorType == "Gravity":
                    if current_time > self.time_old:
                        reading = calcGravity(tilt_cache[self.color]['Gravity'], self.unitsGravity)
                        reading = calibrate(reading, self.calibration_equ)
                        reading = round(reading, 3)
                        self.time_old = current_time
                        self.value = reading
                        self.log_data(self.value)
                elif self.sensorType == "Temperature":
                    self.TEMP_UNIT=self.get_config_value("TEMP_UNIT", "C")
                    if current_time > self.time_old:
                        reading = calcTemp(tilt_cache[self.color]['Temp'],self.TEMP_UNIT)
                        reading = round(reading, 2)
                        self.time_old = current_time 
                        self.value=reading
                        self.log_data(self.value)
                        self.push_update(self.value)
                else:
                    if current_time > self.time_old:
                        reading = tilt_cache[self.color]['RSSI']
                        self.time_old = current_time 
                        self.value=reading
                        self.log_data(self.value)
                        self.push_update(self.value)
                        
                self.push_update(self.value,False)

            await asyncio.sleep(2)
    
    def get_state(self):
        return dict(value=self.value)

def setup(cbpi):
    global tilt_proc
    global tilt_manager
    global tilt_cache
    print ("INITIALIZE TILT MODULE")
    
    tilt_manager = Manager()
    tilt_cache = tilt_manager.dict()

    tilt_proc = Process(name='readTilt', target=readTilt, args=(tilt_cache,))
    tilt_proc.daemon = True
    tilt_proc.start()
    cbpi.plugin.register("BLE Hydrom", BLESensor)
    pass
