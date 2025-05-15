import requests
import json
import os
import time
import shutil
import datetime as dt


def get_weather_data(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=de"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        return None
    except requests.exceptions.RequestException as err:
        print(err)
        return None
    return response.json()

def get_weather_forecast(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=de"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        return None
    except requests.exceptions.RequestException as err:
        print(err)
        return None
    return response.json()

def save_weather_data(data, filename):
    temp_akut = round(data['main']['temp'])
    temp_min = round(data['main']['temp_min'])
    temp_max = round(data['main']['temp_max'])
    humidity = round(data['main']['humidity'])

    save = {
        'city': data['name'],
        'akt_temperature': f"{temp_akut}°C",
        'min_temperature': f"{temp_min}°C",
        'max_temperature': f"{temp_max}°C",
        'humidity': f"{humidity}%",
        'weather': data['weather'][0]['description'],
        'icon': data['weather'][0]['icon']
    }
    with open(filename, 'w') as json_file:
        json.dump(save, json_file, indent=4)
    print(f"Wetterdaten wurden in {filename} gespeichert.")

def save_weather_forecast(data, filename):
    forecast_data = {}
    day_conter = 0
    for entry in data['list']:
        date, time = entry['dt_txt'].split(' ')
        if date == dt.datetime.now().strftime('%Y-%m-%d'):
            continue
        if date not in forecast_data:
            forecast_data[date] = {
            'min_temperature': entry['main']['temp_min'],
            'max_temperature': entry['main']['temp_max'],
            'weather': entry['weather'][0]['description'],
            'icon': entry['weather'][0]['icon']
            }
        else:
            forecast_data[date]['min_temperature'] = min(forecast_data[date]['min_temperature'], entry['main']['temp_min'])
            forecast_data[date]['max_temperature'] = max(forecast_data[date]['max_temperature'], entry['main']['temp_max'])
            if time == '12:00:00':  # Aktualisiere die Wetterbeschreibung und das Icon um 12:00 Uhr
                forecast_data[date]['weather'] = entry['weather'][0]['description']
                forecast_data[date]['icon'] = entry['weather'][0]['icon']
                source_folder = 'Datenback_images'
                output_folder = 'output'
                os.makedirs(output_folder, exist_ok=True)
                weather_icon_file_in = os.path.join(source_folder, f"{entry['weather'][0]['icon']}.png")
                weather_icon_file_out = os.path.join(output_folder, f'{data}.png')
                print(f"das ist das wetter Bild{weather_icon_file_out}")
                copy_and_rename_image(source_folder, entry['weather'][0]['icon'], output_folder, f"{date}.png")
                day_conter += 1

        daily_forecast = []
        for date, data in forecast_data.items():
            daily_forecast.append({
            'date': date,
            'min_temperature': f"{round(data['min_temperature'])}°C",
            'max_temperature': f"{round(data['max_temperature'])}°C",
            'weather': data['weather'],
            'icon': data['icon']
        })
        
        if day_conter == 3:
            break
    with open(filename, 'w') as json_file:
        json.dump(daily_forecast, json_file, indent=4)

    print(f"Wettervorhersage wurde in {filename} gespeichert.")

def copy_and_rename_image(source_folder, icon_code, destination_folder, new_filename):
    print(f"Kopiere Bild {icon_code}.png...")
    source_file = os.path.join(source_folder, f"{icon_code}.png")
    destination_file = os.path.join(destination_folder, new_filename)
    if os.path.exists(source_file):
        shutil.copy(source_file, destination_file)
        print(f"Bild {source_file} wurde nach {destination_file} kopiert.")
    else:
        print(f"Bild {source_file} wurde nicht gefunden.")

def auto_update_wetterdaten():
    with open('output/auto_update_status.json', 'r') as json_file:
        data = json.load(json_file)
        auto_update = data['auto_update']
    while auto_update == True:
        main()
        time.sleep(3600)


def main():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        raise Exception("API-Key nicht gesetzt!")
    city = 'Berlin'
    output_folder = 'output'  # Ordner, in dem die Dateien gespeichert werden sollen
    source_folder = 'Datenback_images'  # Ordner, in dem die Originalbilder gespeichert sind
    os.makedirs(output_folder, exist_ok=True)
    weather_data = get_weather_data(api_key, city)
    weather_forecast = get_weather_forecast(api_key, city)

    if weather_data:            
        weather_data_file = os.path.join(output_folder, 'wetterdaten.json')
        weather_icon_file = os.path.join(output_folder, 'wetter_icon.png')
        save_weather_data(weather_data, weather_data_file)
        copy_and_rename_image(source_folder, weather_data['weather'][0]['icon'], output_folder, 'wetter_icon.png')
        
        print(f"Wetterdaten für {city} wurden in {weather_data_file} gespeichert.")
        print(f"Wetter-Icon wurde als {weather_icon_file} gespeichert.")
    
    if weather_forecast:
        print(f"Wettervorhersage für {city} wurde abgerufen.")
        forecast_file = os.path.join(output_folder, 'wettervorhersage.json')
        save_weather_forecast(weather_forecast, forecast_file)


if __name__ == "__main__":
    with open('output/auto_update_status.json', 'r') as json_file:
        data = json.load(json_file)
    data['auto_update'] = True
    with open('output/auto_update_status.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)
    auto_update_wetterdaten()
    # main()