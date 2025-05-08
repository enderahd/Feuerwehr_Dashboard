import json

def generate_weather_icon_links():
    # Liste der Wetterbedingungen und ihrer entsprechenden Icon-Codes
    weather_conditions = {
        "Klarer Himmel": "01d",#
        "Ein paar Wolken": "02d",#
        "Überwiegend bewölkt": "03d",#
        "Bewölkt": "04d",#
        "Nieselregen": "09d",#
        "Regen": "10d",#
        "Gewitter": "11d",#
        "Schnee": "13d",#
        "Nebel": "50d",#
        "Klarer Himmel (Nacht)": "01n",
        "Ein paar Wolken (Nacht)": "02n",
        "Überwiegend bewölkt (Nacht)": "03n",
        "Bewölkt (Nacht)": "04n",#
        "Nieselregen (Nacht)": "09n",
        "Regen (Nacht)": "10n",#
        "Gewitter (Nacht)": "11n",#
        "Schnee (Nacht)": "13n",#
        "Nebel (Nacht)": "50n"#
    }

    # Basis-URL für die Wetter-Icons
    base_url = "http://openweathermap.org/img/wn/"

    # Generiere die Links zu den Wetter-Icons
    weather_icon_links = {condition: f"{base_url}{icon_code}@4x.png" for condition, icon_code in weather_conditions.items()}

    # Speichere die Links in einer JSON-Datei
    with open('weather_icon_links.json', 'w') as json_file:
        json.dump(weather_icon_links, json_file, indent=4)

    print("Die Links zu den Wetter-Icons wurden in 'weather_icon_links.json' gespeichert.")

if __name__ == "__main__":
    generate_weather_icon_links()