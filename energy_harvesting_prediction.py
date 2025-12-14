import pvlib
import pandas as pd
from datetime import date, datetime, timedelta

# ---- Inputs ----
latitude = 35.0  # degrees
longitude = -120.0  # degrees
tz = 'US/Pacific'  # timezone of the location
surface_tilt = 30  # degrees
surface_azimuth = 180  # 180° = south-facing
module_efficiency = 0.18
system_area = 1.0 * 1.0

location = pvlib.location.Location(latitude, longitude, tz=tz)
today = date.today().strftime("%Y-%m-%d")


def get_predictions(timeslots: int):
    periods = int(24 * 60 / timeslots)
    time = datetime.strptime("16:00", "%H:%M")
    energy_harvesting_values = []
    for i in range(timeslots):
        times = pd.date_range(today + " " + datetime.strftime(time, "%H:%M"), periods=periods, freq='1min', tz=tz)
        clearsky = location.get_clearsky(times)
        solar_position = location.get_solarposition(times)
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt,
            surface_azimuth,
            solar_position['zenith'],
            solar_position['azimuth'],
            clearsky['dni'],
            clearsky['ghi'],
            clearsky['dhi']
        )
        power_dc = poa['poa_global'] * system_area * module_efficiency  # watts
        energy_Wh = power_dc.sum() * (1 / 60)
        energy_harvesting_values.append(energy_Wh)
        time = time + timedelta(minutes=periods)
    return energy_harvesting_values


def prediciton_to_slots(predictions, slot_size_Wh):
    return list(map(lambda val: round(val / slot_size_Wh), predictions))


prediction = get_predictions(24)
print(prediciton_to_slots(prediction, 5))
