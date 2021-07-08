import csv
import datetime
import os
import re

import lxml
from bs4 import BeautifulSoup

from ndfd_xml_client import MPUD


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


def check_cities_csv_integrity(filepath):
    with open(filepath, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        if csvreader.fieldnames != ['City', 'Latitude', 'Longitude']:
            return False
        for row in csvreader:
            try:
                float(row['Latitude'])
                float(row['Longitude'])
            except ValueError:
                return False
    return True


def create_target_datetime():
    target_date = datetime.date.today() + datetime.timedelta(days=1)
    return datetime.datetime(target_date.year, target_date.month, target_date.day, 12)


def is_error_or_none(response):
    if response is None or response.status_code != 200:
        return True
    soup = BeautifulSoup(response.text, 'lxml')
    if soup.find('error'):
        return True
    return False


def update_last_query_time(xml_str):
    soup = BeautifulSoup(xml_str, 'lxml')
    creation_date = soup.find('creation-date')
    if creation_date:
        with open('./program_data/last_query_time.txt', 'w') as txtfile:
            txtfile.write(creation_date.text.replace('Z', '+00:00'))


def create_cities_list(cities_csv):
    cities = []
    with open(cities_csv, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            cities.append(row['City'])
    return cities


def build_and_save_wx_forecast_txtfile(xml_str, target_datetime, cities_filepath):
    soup = BeautifulSoup(xml_str, 'lxml')
    dates_list = soup.find('time-layout').find_all('start-valid-time')
    for index in range(len(dates_list)):
        if datetime.datetime.fromisoformat(dates_list[index].text).date() == target_datetime.date():
            break
    maxt_list = []
    for temp in soup.find_all('temperature'):
        maxt_list.append(temp.find_all('value')[index].text)

    cities_list = create_cities_list(cities_filepath)

    try:
        with open('./program_data/linebreaks.txt', 'r') as br_file:
            linebreak_cities = br_file.read().split('\n')
    except FileNotFoundError:
        linebreak_cities = []

    txt_filename = f'./weather_reports/{target_datetime.date()}_wx_forecast.txt'
    i = 1
    while os.path.exists(txt_filename):
        if not re.match(r'.*\(\d+\)\.txt$', txt_filename):
            txt_filename = txt_filename[:-4] + '(' + str(i) + ').txt'
        else:
            txt_filename = txt_filename[:-6] + str(i) + ').txt'
            i += 1

    with open(txt_filename, 'w') as wx_forecast_file:
        wx_forecast_file.write('City - Daily Maximum Temperature\n\n')
        for index in range(len(cities_list)):
            wx_forecast_file.write(cities_list[index] + ' - ' + maxt_list[index] + '\n')
            if cities_list[index] in linebreak_cities:
                wx_forecast_file.write('\n')


def cleanup_xml_files(xml_limit):
    try:
        dir_list = os.listdir('./program_data/xml/')
    except FileNotFoundError:
        return
    xmls = list(filter(lambda file_name: re.match(r'^\d{14}_t\.xml$', file_name), dir_list))
    if len(xmls) > xml_limit:
        xmls.sort()
        xmls_to_remove = xmls[:-xml_limit]
        for xml in xmls_to_remove:
            os.remove('./program_data/xml/' + xml)


def main():
    print()

    # Pre-runtime checks
    cities_filepath = './program_data/cities.csv'
    if not os.path.exists(cities_filepath):
        print('PROGRAM INTERRUPTED! The file "cities.csv" could not be found.')
        input('Press "enter" to close the program.')
        return
    if not check_cities_csv_integrity(cities_filepath):
        print('PROGRAM INTERRUPTED! The file "cities.csv" is not properly formatted.')
        input('Press "enter" to close the program.')
        return
    if is_on_cooldown():
        print('The program is on cooldown. The duration of cooldown is 1 hour from the last completed runtime.')
        input('Press "enter" to close the program.')
        return

    # Build the query
    target_datetime = create_target_datetime()
    wx_query = MPUD(
        product='time-series',
        begin=target_datetime,
        end=target_datetime,
        ndfd_elements=['maxt']
    )
    wx_query.import_list_lat_lon_from_csv(cities_filepath)

    # Send the query and log the response
    wx_query.send_query()
    wx_query.save_xml('./program_data/xml/')
    response = wx_query.get_response()
    if is_error_or_none(response):
        print('The NDFD REST API returned an error.')
        input('Press "enter" to close the program.')
        return
    update_last_query_time(response.text)
    build_and_save_wx_forecast_txtfile(response.text, target_datetime, cities_filepath)

    # Wrap things up
    cleanup_xml_files(30)
    print('The program has finished.')
    input('Press "enter" to close the program.')


if __name__ == "__main__":
    main()
