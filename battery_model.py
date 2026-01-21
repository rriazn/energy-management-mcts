import energy_harvesting_prediction as ehp
from datetime import date, datetime, timedelta

def calculate_battery_discharge(task_cost_mA):
    hours_until_empty = (max_battery_charge * battery_voltage * battery_count) / (task_cost_mA * battery_load_voltage)
    print(hours_until_empty)
    current_draw_per_hour = max_battery_charge / hours_until_empty
    battery = max_battery_charge
    hour = 0
    while True:
        print(f"{battery}")
        if battery - current_draw_per_hour < 0:
            break
        battery -= current_draw_per_hour
        hour += 1
    print(f"0")


def calculate_battery_charge():
    day = date(2026, 1, 1)
    for i in range(12):
        hours = 0
        battery = 0
        while battery < max_battery_charge:
            energy_pred = ehp.get_energy_predictions_clearsky(24, day.strftime("%Y-%m-%d"))
            for e in energy_pred:
                battery += battery_efficiency * e
                hours += 1
                if battery >= max_battery_charge:
                    break
            if battery >= max_battery_charge:
                break
            day = day + timedelta(days=1)
        print(f"{day.month}\t{hours}")
        if i != 11:
            day = date(day.year, day.month + 1, 1)



max_battery_charge = 2500 #mAh
battery_voltage = 1.5 #V
battery_count = 2
battery_load_voltage = 3.3

battery_efficiency = 1 # ideal

calculate_battery_charge()