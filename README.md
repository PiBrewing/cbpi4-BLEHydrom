# DO NOT USE THIS BRANCH - ONLY FOR TESTING WITH BLEAK AS BLE API

# CraftbeerPi4 Sensor Plugin for Hydrom / Tilt

Allows your Hydrom or Tilt digital hydrometer to send data to CraftBeerPi 4.0, such as the current temperature and gravity readings. The plugin allows you to create multiple sensors, each of which is associated with a different data type that the device is capturing, so that you can use these sensors as you would any other sensor in CraftBeerPi4. You can also use multiple Hydrom or/and Tilt devices for different fermentation chambers at the same time. See below for setup instructions and some screenshots of the configuration options.

The ble beacon scan of the plugin is based on this code: https://koen.vervloesem.eu/blog/decoding-bluetooth-low-energy-advertisements-with-python-bleak-and-construct/

## Requirements

You need to run this on a Raspberry that has bluetooth onboard or a bluetooth dongle installed. Bluetooth needs to be enabled.

## Installation

Please follow th instructions from the [documentation](https://openbrewing.gitbook.io/craftbeerpi4_support/readme/plugin-installation).

- Package name:  cbpi4-BLEHydrom

- Package Github link: https://github.com/pibrewing/cbpi4-BLEHydrom/archive/main.zip

If bluetooth is blocked, you need to activate it manually

Check first, if the bluetooth service is blocked:

`sudo rfkill list`

This will give you the following output if bluetooth is blocked:

```
0: hci0: Bluetooth
        Soft blocked: yes
        Hard blocked: no
1: phy0: Wireless LAN
        Soft blocked: no
        Hard blocked: no
```

Run the command `sudo rfkill unblock bluetooth` to activated bluetoth on the pi

Another `sudo rfkill list` should show:

```
0: hci0: Bluetooth
        Soft blocked: no
        Hard blocked: no
1: phy0: Wireless LAN
        Soft blocked: no
        Hard blocked: no
```

Then the softblock is disabled and the plugin should be working

## Configuration

### CraftBeerPi Configuration
1. In CraftBeerPi, click on the side menu, and then choose **Hardware**.
2. Click the **Add** button in the Sensor section, and fill out the sensor properties:
    1. **Name**: Give the sensor a name. This is specific to this sensor reading, and does not need to match the Tilt color. It can be something like Wort Gravity or Tilt Temperature.
    2. **Type**: Choose BLEHydrom.
    3. **Tilt Color**: This should be set to the color of your Tilt or color config of your Hydrom.
    4. **Hardware**: Here you must select if you are using a Tilt / Hydrom or one of the Tilt pro series. Pro series devices can be used in parallel with a Tilt or Hydrom of the same color.
    5. **Data Type**: Each Tilt has three types of data that it reports, the Temperature,Gravity and RSSI, so select the one that you are configuring for this particular sensor. 
    6. **Gravity Units**: *This field is only required if Data Type is set to Gravity*. The Tilt converts its readings into Specific Gravity by default. However you can choose one of three types here and it will be converted to that unit automatically. The choices are SG (Specific Gravity), Brix (or °Bx), and Plato (or °P).
    7. **Calibration Point 1-3***: *Optional*. These fields allow you to calibrate your Tilt by entering an uncalibrated reading from the Tilt and then the desired, calibrated value. The format to use is ***uncalibrated value* = *actual value*** (spacing is optional). More info on calibration is in the section below.
    8. Once you have filled out the sensor fields, click **Add**.
3. Repeat the above steps if you want additional sensors for the other data types that your Tilt reports, or if you have more than one Tilt, you can create sensors for those devices as well.
4. You can now add any of the Tilt sensors to kettles or fermenters in your brewery, or you can view their data on the dashboard or graph their data with the charts.

### Tilt Calibration
You can use the Calibration Point fields to calibrate your Tilt, much like when using the standalone Tilt app. Here are some examples of ways you can calibrate your Tilt with this plugin.

- You can perform the *Tare in Water* procedure by placing the Tilt in water, taking a reading, and entering the value in a Calibration Point field in the format **1.002 = 1** (change the first number to your specific reading). 
- To fine tune the calibration even more, you can make a low and/or high gravity calibration point by taking readings of one or two solutions with a known gravity and enter those readings as ***tilt reading* = *solution's actual gravity***.
- If you enter only a single calibration point, the difference will be applied to every reading equally. So you could enter **0 = 5** if you just want 5 added to every reading that the Tilt takes, or **5 = 0** if you want to subtract 5 from every reading.  If you enter two or more calibration points, a linear relationship between the points will be determined and used to adjust the readings accordingly (known as linear regression).
- These calibration procedures work the same for both gravity readings and temperature readings, and are calculated after the conversion to the desired units (°C to °F, SG to Brix), so you should calibrate your Tilt with the units set to what they will be when you use it for actual brewing.


### Changelog:

- 02.02.26: (1.0.0 alpha) Usage of bleak
- 31.01.26: (0.0.10) modified blescan under trixie (filter setting) due to issues. Added pyproject.toml file
- 13.07.24: (0.0.8) Addition of Tilt Pro series.
- 13.04.24: (0.0.7) Test with new gattlib-dbus package.
- 10.01.23: (0.0.6) Test with PyBluez Mod as interim solution.
- 01.12.23: (0.0.6.a1) updated requirements.
- 11.05.22: (0.0.5) Updated README (removed cbpi add).
- 25.02.22: (0.0.4) Updated README.
- 16.01.22: (0.0.3) Reduced mqtt traffic (->cbpi 4.0.1.2 required!!).
- 08.01.22: (0.0.2) Added RSSI value from blescan as parameter.
- 07.01.22: (0.0.1) Initial Commit.

