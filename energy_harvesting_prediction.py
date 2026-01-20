import pvlib
import pandas as pd
from datetime import date, datetime, timedelta
import openmeteo_requests
import requests
import requests_cache
from retry_requests import retry


latitude = 51.477
longitude = 0.0        # Greenwich, UK
tz = 'UTC'
surface_tilt = 30
surface_azimuth = 180  # 180° = south-facing
module_efficiency = 0.11
system_area = 0.09 * 0.04
battery_voltage = 3.3   # example, max. for MICAz WIRELESS MEASUREMENT SYSTEM

location = pvlib.location.Location(latitude, longitude, tz=tz)
today = date.today().strftime("%Y-%m-%d")


def get_irradiance_predictions(timeslots):
    # Set up session for open-meteo
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # parameters
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "shortwave_radiation",
            "direct_normal_irradiance",
            "diffuse_radiation"
        ],
        "timezone": "Europe/Berlin"
    }
    responses = requests.get(url, params=params)
    response = responses.json()
    hourly = response["hourly"]
    df = pd.DataFrame({
        "ghi": hourly["shortwave_radiation"],
        "dni": hourly["direct_normal_irradiance"],
        "dhi": hourly["diffuse_radiation"]
    }).to_numpy()
    irr_25h = df[16:25+16]
    irr_timeslots = []
    timeslot_fraction = 24 / timeslots
    hours = 0
    for i in range(timeslots):
        fraction = hours - int(hours)

        # interpolate values
        irr_timeslots.append({
                "ghi": float(fraction * irr_25h[int(hours + 1)][0] + (1 - fraction) * irr_25h[int(hours)][0]),
                "dni": float(fraction * irr_25h[int(hours + 1)][1] + (1 - fraction) * irr_25h[int(hours)][1]),
                "dhi": float(fraction * irr_25h[int(hours + 1)][2] + (1 - fraction) * irr_25h[int(hours)][2]),
            }
        )

        hours += timeslot_fraction
    return irr_timeslots


def get_energy_predictions(timeslots):
    periods = int(24 * 60 / timeslots)
    time = datetime.strptime("16:00", "%H:%M")
    energy_harvesting_values = []
    irradiance = get_irradiance_predictions(timeslots)
    for i in range(timeslots):
        times = pd.date_range(today + " " + datetime.strftime(time, "%H:%M"), periods=periods, freq='1min', tz=tz)
        solar_position = location.get_solarposition(times)
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt,
            surface_azimuth,
            solar_position['zenith'],
            solar_position['azimuth'],
            irradiance[i]['dni'],
            irradiance[i]['ghi'],
            irradiance[i]['dhi']
        )
        power_dc = poa['poa_global'] * system_area * module_efficiency  # watts
        energy_Wh = power_dc.sum() * (1 / 60)
        energy_harvesting_values.append(energy_Wh)
        time = time + timedelta(minutes=periods)
    return energy_harvesting_values


def get_energy_predictions_clearsky(timeslots, date):
    periods = int(24 * 60 / timeslots)
    time = datetime.strptime("16:00", "%H:%M")
    energy_harvesting_values = []
    for i in range(timeslots):
        times = pd.date_range(date + " " + datetime.strftime(time, "%H:%M"), periods=periods, freq='1min', tz=tz)
        solar_position = location.get_solarposition(times)
        clearsky = location.get_clearsky(times)
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
        energy_Wh = power_dc.sum() / 60
        energy_harvesting_values.append(energy_Wh * 1000 / battery_voltage)
        time = time + timedelta(minutes=periods)
    return energy_harvesting_values


def prediciton_to_slots(predictions, slot_size_Wh):
    return list(map(lambda val: round(val / slot_size_Wh), predictions))


def avg_monthly_firstday_energy(year):
    timeslots = 24
    monthly_energies = []

    for month in range(1, 13):
        d = date(year, month, 1).strftime("%Y-%m-%d")
        energy = get_energy_predictions_clearsky(timeslots, d)
        monthly_energies.append(sum(energy) / len(energy))

    # Print results
    print(f"Average incoming energy per hour (Wh) for {year} (1st of each month):")
    for m, val in enumerate(monthly_energies):
        print(float(val))



#prediction = get_energy_predictions(24)
#print(prediciton_to_slots(prediction, 5))

print(list(map(lambda p: round(p / 10), get_energy_predictions_clearsky(24, date(2026, 6, 1).strftime("%Y-%m-%d")))))
#avg_monthly_firstday_energy(2026)
