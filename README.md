# CraftbeerPi4 Sensor Plugin for Hydrom / Tilt

Allows your Hydrom or Tilt digital hydrometer to send data to CraftBeerPi 4.0, such as the current temperature and gravity readings. The plugin allows you to create multiple sensors, each of which is associated with a different data type that the device is capturing, so that you can use these sensors as you would any other sensor in CraftBeerPi4. You can also use multiple Hydrom or/and Tilt devices for different fermentation chambers at the same time. See below for setup instructions and some screenshots of the configuration options.

The plugin is poerted from the CraftbeerPi3 plugin Version (https://github.com/IndyJoeA/cbpi_Tilt)

## Requirements

You need to run this on a Raspberry that has bluetooth onboard or a bluetooth dongle installed. Bluetooth needs to be enabled.

## Installation

Before you can install this plugin, you will need to install a couple of additional packages manually. The plugin has been only tested yet with Raspberry Pi Bullseye 32 bit where it is confirmed to be working with the Hydrom and the Tilt

 
`sudo apt-get install pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev libglib2.0-dev python3-dev`

Once these packages have been isntalled, you need to install and activate the plugin on your system. 

You can either install it directly from pypi.org via:

`sudo pip3 install cbpi4-BLEHydrom`

or from the GITHub repo via:

`sudo pip3 install https://github.com/avollkopf/cbpi4-BLEHydrom/archive/main.zip`

Afterwards, you need to activate it in cbpi with the following command (this won't be required for future versions of cbpi):

`cbpi add cbpi4-BLEHydrom`

## Configuration

### CraftBeerPi Configuration
1. In CraftBeerPi, click on the side menu, and then choose **Hardware**.
2. Click the **Add** button in the Sensor section, and fill out the sensor properties:
    1. **Name**: Give the sensor a name. This is specific to this sensor reading, and does not need to match the Tilt color. It can be something like Wort Gravity or Tilt Temperature.
    2. **Type**: Choose BLEHydrom.
    3. **Tilt Color**: This should be set to the color of your Tilt or color config of your Hydrom
    4. **Data Type**: Each Tilt has three types of data that it reports, the Temperature,Gravity and RSSI, so select the one that you are configuring for this particular sensor. 
    5. **Gravity Units**: *This field is only required if Data Type is set to Gravity*. The Tilt converts its readings into Specific Gravity by default. However you can choose one of three types here and it will be converted to that unit automatically. The choices are SG (Specific Gravity), Brix (or °Bx), and Plato (or °P).
    6. **Calibration Point 1-3***: *Optional*. These fields allow you to calibrate your Tilt by entering an uncalibrated reading from the Tilt and then the desired, calibrated value. The format to use is ***uncalibrated value* = *actual value*** (spacing is optional). More info on calibration is in the section below.
    7. Once you have filled out the sensor fields, click **Add**.
3. Repeat the above steps if you want additional sensors for the other data types that your Tilt reports, or if you have more than one Tilt, you can create sensors for those devices as well.
4. You can now add any of the Tilt sensors to kettles or fermenters in your brewery, or you can view their data on the dashboard or graph their data with the charts.

### Tilt Calibration
You can use the Calibration Point fields to calibrate your Tilt, much like when using the standalone Tilt app. Here are some examples of ways you can calibrate your Tilt with this plugin.

- You can perform the *Tare in Water* procedure by placing the Tilt in water, taking a reading, and entering the value in a Calibration Point field in the format **1.002 = 1** (change the first number to your specific reading). 
- To fine tune the calibration even more, you can make a low and/or high gravity calibration point by taking readings of one or two solutions with a known gravity and enter those readings as ***tilt reading* = *solution's actual gravity***.
- If you enter only a single calibration point, the difference will be applied to every reading equally. So you could enter **0 = 5** if you just want 5 added to every reading that the Tilt takes, or **5 = 0** if you want to subtract 5 from every reading.  If you enter two or more calibration points, a linear relationship between the points will be determined and used to adjust the readings accordingly (known as linear regression).
- These calibration procedures work the same for both gravity readings and temperature readings, and are calculated after the conversion to the desired units (°C to °F, SG to Brix), so you should calibrate your Tilt with the units set to what they will be when you use it for actual brewing.


###Changelog:

- 25.02.22: (0.0.4) Updated README
- 16.01.22: (0.0.3) Reduced mqtt traffic (->cbpi 4.0.1.2 required!!)
- 08.01.22: (0.0.2) Added RSSI value from blescan as parameter
- 07.01.22: (0.0.1) Initial Commit

