from __future__ import print_function

import datetime
import os
import sys
import time
from urllib import urlencode

import urllib2
from sense_hat import SenseHat

from config import Config
# Constants
# Minutes
MEASUREMENT_INTERVAL = 5
# Feltoltsuk a Weather Underground-ra?
WEATHER_UPLOAD = False



WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
SINGLE_HASH = "#"
HASHES = "########################################"
SLASH_N = "\n"

b = [0, 0, 255]  # blue
r = [255, 0, 0]  # red
e = [0, 0, 0]  # empty

arrow_up = [
    e, e, e, r, r, e, e, e,
    e, e, r, r, r, r, e, e,
    e, r, e, r, r, e, r, e,
    r, e, e, r, r, e, e, r,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e
]
arrow_down = [
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    b, e, e, b, b, e, e, b,
    e, b, e, b, b, e, b, e,
    e, e, b, b, b, b, e, e,
    e, e, e, b, b, e, e, e
]
bars = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    r, r, r, r, r, r, r, r,
    r, r, r, r, r, r, r, r,
    b, b, b, b, b, b, b, b,
    b, b, b, b, b, b, b, b,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e
]


def c_to_f(input_temp):
    return (input_temp * 1.8) + 32


def get_cpu_temp():
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=", "").replace("'C\n", ""))


def get_smooth(x):
    if not hasattr(get_smooth, "t"):
        get_smooth.t = [x, x, x]
    get_smooth.t[2] = get_smooth.t[1]
    get_smooth.t[1] = get_smooth.t[0]
    get_smooth.t[0] = x

    xs = (get_smooth.t[0] + get_smooth.t[1] + get_smooth.t[2]) / 3
    return xs


def get_temp():
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    t = (t1 + t2) / 2
    t_cpu = get_cpu_temp()
    # Korrigaljuk a cpu melegitese miatti pontatlansagot
    t_corr = t - ((t_cpu - t) / 1.5)
    t_corr = get_smooth(t_corr)
    return t_corr


def main():
    global last_temp
    last_minute = datetime.datetime.now().minute
    last_minute -= 1
    if last_minute == 0:
        last_minute = 59

    while 1:
        current_second = datetime.datetime.now().second
        if (current_second == 0) or ((current_second % 10) == 0):
            calc_temp = get_temp()
            temp_c = round(calc_temp, 1)
            temp_f = round(c_to_f(calc_temp), 1)
            humidity = round(sense.get_humidity(), 0)
            pressure = round(sense.get_pressure() * 0.0295300, 1)
            print("Temp: %sC (%sF), Pressure: %s inHg, Humidity: %s%%" % (temp_c, temp_f, pressure, humidity))
            current_minute = datetime.datetime.now().minute
            if current_minute != last_minute:
                last_minute = current_minute
                if (current_minute == 0) or ((current_minute % MEASUREMENT_INTERVAL) == 0):
                    now = datetime.datetime.now()
                    print("\n%d minute mark (%d @ %s)" % (MEASUREMENT_INTERVAL, current_minute, str(now)))
                    if last_temp != temp_c:
                        if last_temp > temp_c:
                            sense.set_pixels(arrow_down)
                        else:
                            sense.set_pixels(arrow_up)
                    else:
                        sense.set_pixels(bars)
                    last_temp = temp_c
                    if WEATHER_UPLOAD:
                        print("Uploading data to Weather Underground")
                        weather_data = {
                            "action": "updateraw",
                            "ID": wu_station_id,
                            "PASSWORD": wu_station_key,
                            "dateutc": "now",
                            "tempf": str(temp_f),
                            "humidity": str(humidity),
                            "baromin": str(pressure),
                        }
                        try:
                            upload_url = WU_URL + "?" + urlencode(weather_data)
                            response = urllib2.urlopen(upload_url)
                            html = response.read()
                            print("Server response:", html)
                            response.close()
                        except:
                            print("Exception:", sys.exc_info()[0], SLASH_N)
                    else:
                        print("Skipping Weather Underground upload")
        time.sleep(1)


print("\n" + HASHES)
print(SINGLE_HASH, "Pi Weather Station                  ", SINGLE_HASH)
print(HASHES)

if (MEASUREMENT_INTERVAL is None) or (MEASUREMENT_INTERVAL > 60):
    print("The application's 'MEASUREMENT_INTERVAL' cannot be empty or greater than 60")
    sys.exit(1)

print("\nInitializing Weather Underground configuration")
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
if (wu_station_id is None) or (wu_station_key is None):
    print("Missing values from the config file\n")
    sys.exit(1)

print("Successfully read config values")
print("Station ID:", wu_station_id)


try:
    print("Initializing the Sense HAT client")
    sense = SenseHat()
    sense.show_message("Init", text_colour=[255, 255, 0], back_colour=[0, 0, 255])
    sense.clear()
    last_temp = round(get_temp(), 1)
    print("Current temperature reading:", last_temp , "C")
except:
    print("Unable to initialize the Sense HAT library:", sys.exc_info()[0])
    sys.exit(1)

print("Initialization complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting application\n")
        sys.exit(0)
