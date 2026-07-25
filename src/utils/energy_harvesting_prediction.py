import numpy as np
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
battery_voltage = 3.3

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


def get_wind_energy_predictions(timeslots,
                                date="2023-06-15",
                                rotor_diameter=0.5,     # meters
                                cp=0.5,                 # power coefficient
                                air_density=1.225,      # kg/m³
                                cut_in=0.0,             # m/s
                                rated_speed=12,       # m/s
                                cut_out=100.0):          # m/s
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date,
        "end_date": date,
        "hourly": "wind_speed_10m",
        "timezone": "Europe/Berlin"
    }

    response = requests.get(url, params=params)
    data = response.json()
    wind_speeds = np.array(data["hourly"]["wind_speed_10m"])  # 24 values
    #print(wind_speeds, len(wind_speeds))

    A = np.pi * (rotor_diameter / 2) ** 2 # turbine swept area

    power_hourly = []
    for v in wind_speeds:
        if v < cut_in or v > cut_out:
            P = 0
        elif v <= rated_speed:
            P = 0.5 * air_density * A * cp * v**3
        else:
            # constant rated power beyond rated speed
            P = 0.5 * air_density * A * cp * rated_speed**3
        power_hourly.append(P)

    power_hourly = np.array(power_hourly) # watts

    timeslot_fraction = 24 / timeslots
    hours = 0
    energy_timeslots = []
    # interpolate to timeslots
    for _ in range(timeslots):
        fraction = hours - int(hours)

        P_interp = (
            fraction * power_hourly[min(int(hours + 1), 23)]
            + (1 - fraction) * power_hourly[int(hours)]
        )

        # Energy = Power * slot time
        slot_hours = timeslot_fraction
        energy_Wh = P_interp * slot_hours

        energy_timeslots.append(float(energy_Wh))
        hours += timeslot_fraction

    return energy_timeslots


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
        energy_harvesting_values.append(energy_Wh * 1000 / battery_voltage) # mAh
        time = time + timedelta(minutes=periods)
    return energy_harvesting_values


def get_energy_from_pvgis(lines):
    energy_harvesting_values = []

    for index, row in lines.iterrows():
        ghi = float(row["G(i)"])  # G(h) in W/m²

        energy_wh = ghi * system_area * module_efficiency
        charge_mah = energy_wh * 1000 / battery_voltage

        energy_harvesting_values.append(charge_mah)

    return energy_harvesting_values


def get_energy_for_day(day):
    assert day.year == 2023, "year has to be 2023"
    end_time = day + timedelta(hours=24)
    result = df[(df['datetime'] >= day) & (df['datetime'] < end_time)]
    return get_energy_from_pvgis(result)


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
K = 24
#energy_vals = list(map(lambda p: round(round(p / (10 * (24 / K)))), get_energy_predictions_clearsky(K, date(2023, 4, 1).strftime("%Y-%m-%d"))))
#print(energy_vals)

df = pd.read_csv("Timeseries_40.396_-3.611_SA3_1kWp_crystSi_11_30deg_0deg_2023_2023.csv", skiprows=8, nrows=8760)
df["datetime"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M")

#print(list(map(lambda p: round(p), get_energy_for_day(datetime(2023, 1, 7, 16, 10)))))
'''
b = 0
print(b)
for xi in r:
    b+=xi
    print(b)
'''
print(list(map(lambda p: round(p / 10), get_energy_predictions_clearsky(24, date(2026, 4, 1).strftime("%Y-%m-%d")))))
#energy_vals = get_energy_from_pvgis(lines)
#for v in energy_vals:
    #print(round(v / 20))
#avg_monthly_firstday_energy(2026)
# Parse the time column
'''
df['time'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M')

# Group by year and month, then average the irradiance
df['year_month'] = df['time'].dt.to_period('M')

monthly_avg = df.groupby('year_month')['G(i)'].mean().reset_index()
monthly_avg.columns = ['month', 'avg_irradiance']

print(monthly_avg)
'''
print(list(map(lambda p: round(p/10), get_wind_energy_predictions(24))))
