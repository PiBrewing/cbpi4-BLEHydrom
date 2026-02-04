
# -*- coding: utf-8 -*-
from multiprocessing import Process, Manager
import time
import os
from aiohttp import web
import logging
from unittest.mock import MagicMock, patch
import asyncio

from uuid import UUID

from construct import Array, Byte, Const, Int8sl, Int16ub, Struct
from construct.core import ConstError

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from cbpi.api import *


logger = logging.getLogger(__name__)

import numpy as np

global cache

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

ibeacon_format = Struct(
    "type_length" / Const(b"\x02\x15"),
    "uuid" / Array(16, Byte),
    "major" / Int16ub,
    "minor" / Int16ub,
    "power" / Int8sl,
)


class BLE_init(CBPiExtension):

    def __init__(self, cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_scanner())

    def device_found(self,
        device: BLEDevice, advertisement_data: AdvertisementData
    ):
        """Decode iBeacon."""
        try:
            apple_data = advertisement_data.manufacturer_data[0x004C]
            ibeacon = ibeacon_format.parse(apple_data)
            uuid = UUID(bytes=bytes(ibeacon.uuid))
            uuid = str(uuid).replace("-", "")
            beacon={
                        'uuid': uuid,
                        'major': ibeacon.major,
                        'minor': ibeacon.minor,
                        'rssi': advertisement_data.rssi
                    }
            if beacon['uuid'] in TILTS.keys():
                time_new=time.time()
                set_cache=False
                if int(beacon['minor']) < 2000:
                    try:
                        time_old = float(cache[TILTS[beacon['uuid']]+"_0"]["Time"])
                        if (time_new - time_old) > 15:
                            set_cache=True
                    except:
                        set_cache=True
                    # Tilt regular or Hydrom
                    if set_cache == True:
                        cache[TILTS[beacon['uuid']]+"_0"] = {'Temp': beacon['major'], 'Gravity': beacon['minor'], 'Time': time_new,'RSSI': beacon['rssi']}
                        logging.error(cache)
                else:
                    try:
                        time_old = float(cache[TILTS[beacon['uuid']]+"_1"]["Time"])
                        if (time_new - time_old) > 5:
                            set_cache=True
                    except:
                        set_cache=True
                    # Tilt mini pro
                    if set_cache == True:
                        temp=float(beacon['major'])/10
                        gravity=float(beacon['minor'])/10
                        cache[TILTS[beacon['uuid']]+"_1"] = {'Temp': temp, 'Gravity': gravity, 'Time': time_new,'RSSI': beacon['rssi']}
                        logging.error(cache)


        except KeyError:
            # Apple company ID (0x004c) not found
            pass
        except ConstError:
            # No iBeacon (type 0x02 and length 0x15)
            pass

    async def init_scanner(self):
        """Scan for devices."""
        try:
            scanner = BleakScanner(self.device_found)
        except Exception as e:
            logging.error("BLE Scanner could not be started: {}".format(e))
            return
        
        while True:
            try:
                await scanner.start()
                await asyncio.sleep(1.0)
                await scanner.stop()
            except Exception as e:
                logging.error("Error during BLE scanning: {}".format(e)) 
                await asyncio.sleep(10.0)  # Wait before retrying   
            

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
	
@parameters([Property.Select(label="Sensor color", options=["Red", "Green", "Black", "Purple", "Orange", "Blue", "Yellow", "Pink"], description="Select the color of your Tilt"),
             Property.Select(label="Hardware", options=["Hydrom / Tilt", "Tilt Pro / Pro Mini"], description="Select the device Type (Default is Hydrom / Tilt)"),
	         Property.Select(label= "Data Type", options=["Temperature", "Gravity","RSSI"], description="Select which type of data to register for this sensor"),
	         Property.Select(label="Gravity Units", options=["SG", "Brix", "Plato"], description="Converts the gravity reading to this unit if the Data Type is set to Gravity"),
	         Property.Text(label="Calibration Point 1", configurable=True, default_value="", description="Optional field for calibrating your Tilt. Enter data in the format uncalibrated=actual"),
             Property.Text(label="Calibration Point 2", configurable=True, default_value="", description="Optional field for calibrating your Tilt. Enter data in the format uncalibrated=actual"),
             Property.Text(label="Calibration Point 3", configurable=True, default_value="", description="Optional field for calibrating your Tilt. Enter data in the format uncalibrated=actual")])
class BLESensor(CBPiSensor):
    
    def __init__(self, cbpi, id, props):
        super(BLESensor, self).__init__(cbpi, id, props)
        global cache
        self.value = 0
        self.calibration_equ=""
        self.x_cal_1=self.props.get("Calibration Point 1","")
        self.x_cal_2=self.props.get("Calibration Point 2","")
        self.x_cal_3=self.props.get("Calibration Point 3","")

        self.device_color=self.props.get("Sensor color","Green")
        self.device = "_0" if self.props.get("Hardware","Hydrom / Tilt") == "Hydrom / Tilt" else "_1"
        self.color = self.device_color + self.device
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
            if self.color in cache:
                current_time = float(cache[self.color]['Time'])
                #logging.info("Color: {} | Time Old: {} | Curent Time: {}".format(self.color,self.time_old,current_time))
                if self.sensorType == "Gravity":
                    if current_time > self.time_old:
                        reading = calcGravity(cache[self.color]['Gravity'], self.unitsGravity)
                        reading = calibrate(reading, self.calibration_equ)
                        reading = round(reading, 4)
                        self.time_old = current_time
                        self.value = reading
                        self.log_data(self.value)
                elif self.sensorType == "Temperature":
                    self.TEMP_UNIT=self.get_config_value("TEMP_UNIT", "C")
                    if current_time > self.time_old:
                        reading = calcTemp(cache[self.color]['Temp'],self.TEMP_UNIT)
                        reading = round(reading, 2)
                        self.time_old = current_time 
                        self.value=reading
                        self.log_data(self.value)
                        self.push_update(self.value)
                else:
                    if current_time > self.time_old:
                        reading = cache[self.color]['RSSI']
                        self.time_old = current_time 
                        self.value=reading
                        self.log_data(self.value)
                        self.push_update(self.value)
                        
                self.push_update(self.value,False)

            await asyncio.sleep(2)
    
    def get_state(self):
        return dict(value=self.value)

def setup(cbpi):
    print ("INITIALIZE TILT MODULE")
    
    cbpi.plugin.register("BLE Hydrom", BLESensor)
    cbpi.plugin.register("BLE_init", BLE_init)
    pass
