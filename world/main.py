import csv
import datetime
import json
import os
import re

import requests


def is_on_cooldown():
    try:
        with open('./program_data/last_query_time.txt', 'r') as txtfile:
            last_query_time = txtfile.read()
        formated_last_query_time = datetime.datetime.fromisoformat(last_query_time)
    except (FileNotFoundError, ValueError):
        return False

    if formated_last_query_time > datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1):
        return True
    return False


def check_cities_txt_integrity(filepath):
    with open(filepath, 'r') as f:
        csvreader = csv.DictReader(f, delimiter=';')
        if csvreader.fieldnames != ['Country', 'City', 'CityId']:
            return False
        for row in csvreader:
            try:
                int(row['CityId'])
            except ValueError:
                return False
    return True


def save_json(responses, timestamp):
    filename = ''.join([char for char in timestamp.isoformat().split('.')[0] if char.isdigit()]) + '_t.json'
    with open(f'./program_data/json/{filename}', 'w') as f:
        json.dump(responses, f)


def save_error(error, timestamp):
    filepath = './program_data/json/error.txt'

    i = 1
    while os.path.exists(filepath):
        filepath = f'./program_data/json/error({i}).txt'
        i += 1

    with open(filepath, 'w') as f:
        f.write(error)


def cleanup_json_files(json_limit):
    try:
        dir_list = os.listdir('./program_data/xml/')
    except FileNotFoundError:
        return
    jsons = list(filter(lambda file_name: re.match(r'^\d{14}_t\.json$', file_name), dir_list))
    if len(jsons) > json_limit:
        jsons.sort()
        jsons_to_remove = jsons[:-json_limit]
        for json_file in jsons_to_remove:
            os.remove('./program_data/json/' + json_file)


def main():
    print()

    # Pre-runtime checks
    cities_filepath = './program_data/cities.txt'
    if not os.path.exists(cities_filepath):
        print('PROGRAM INTERRUPTED! The file "cities.txt" could not be found.')
        input('Press "enter" to close the program.')
        return
    if not check_cities_txt_integrity(cities_filepath):
        print('PROGRAM INTERRUPTED! The file "cities.txt" is not properly formatted.')
        input('Press "enter" to close the program.')
        return
    if is_on_cooldown():
        print('The program is on cooldown. The duration of cooldown is 1 hour from the last completed runtime.')
        input('Press "enter" to close the program.')
        return

    # Setup for the queries
    cities = []
    with open('./program_data/cities.txt', 'r') as f:
        csvreader = csv.DictReader(f, delimiter=';')
        for row in csvreader:
            cities.append((row['Country'], row['City'], row['CityId']))
    timestamp = datetime.datetime.utcnow()

    # Make the queries
    with open('./program_data/last_query_time.txt', 'w') as f:
        f.write(timestamp.isoformat().split('.')[0] + '+00:00')
    responses = []
    for city in cities:
        response = requests.get(f'https://worldweather.wmo.int/en/json/{city[2]}_en.json')
        if response is None or response.status_code != 200:
            if responses:
                save_json(responses, timestamp)
            if response:
                save_error(response.text, timestamp)
                print('The server returned an error.')
            else:
                print('The server did not respond.')
            input('Press "enter" to close the program.')
            return
        responses.append(json.loads(response.text))
    save_json(responses, timestamp)

    # Parse the data
    target_date = datetime.date.today() + datetime.timedelta(days=1)
    forecasts = []
    for response in responses:
        country = response['city']['member']['memName']
        city = response['city']['cityName']
        for day in response['city']['forecast']['forecastDay']:
            if day['forecastDate'] == target_date.isoformat():
                max_temp = day['maxTemp']
                break
        else:
            max_temp = 'N/A'
        forecasts.append((country, city, max_temp))

    # Log the forecasts
    filename = f'{target_date.isoformat()}_wx_forecast.txt'
    i = 1
    while os.path.exists(f'./weather_reports/{filename}'):
        filename = f'{target_date.isoformat()}_wx_forecast({i}).txt'
        i += 1
    try:
        with open('./program_data/linebreaks.txt', 'r') as f:
            linebreaks = f.read()
    except FileNotFoundError:
        linebreaks = ''
    with open(f'./weather_reports/{filename}', 'w') as f:
        f.write('Country - City - Daily Maximum Temperature\n\n')
        for forecast in forecasts:
            f.write(forecast[0] + ' - ' + forecast[1] + ' - ' + forecast[2] + '\n')
            if f'"{forecast[0]}";"{forecast[1]}"' in linebreaks:
                f.write('\n')

    # Wrap things up
    cleanup_json_files(30)
    print('The program has finished.')
    input('Press "enter" to close the program.')


if __name__ == "__main__":
    main()
