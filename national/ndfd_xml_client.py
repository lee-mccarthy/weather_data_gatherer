import csv
import datetime
import os
import re

import lxml
import requests
from bs4 import BeautifulSoup


class MPUD:
    """
    A query-builder for requesting multiple point unsummarized data from
    the NDFD REST API.

    Attributes:
        list_lat_lon (str): Properly formatted string of latitude,longitude
            coordinates. (eg: '40.71,-74.01 34.05,-118.25')
        product (str): Either 'glance' or 'time-series'.
            Defaults to 'glance'.
        begin (datetime.datetime): The start date of the data as UTC.
        end (datetime.datetime): The end date of the data as UTC.
        unit (str): 'e' or None for emperical units,
            'm' for metric units.
        ndfd_elements (tuple): A tuple or list of NDFD elements.

    Methods:
        add_lat_lon_coords(coords):
            Appends additional latitude,longitude coordinates to
            the list_lat_lon attribute.
        import_list_lat_lon_from_csv(csvfilepath):
            Imports latitude,longitude coordinates to the list_lat_lon
            attrubute from a csv file.
        add_ndfd_elements(*elements):
            Adds one or more NDFD elements to the query list.
        remove_ndfd_elements(*elements):
            Removes one or more NDFD elements from the query list.
        send_query():
            Builds the query url and sends an HttpRequest to the
            NDFD REST API.
        get_response():
            Returns the entire response object that was recieved from the
            NDFD REST API, or returns None if there is no response.
        save_xml(filepath=''):
            Saves to disk the xml file recieved in the response from the
            NDFD REST API, or returns 0 if there is no response.
    """

    __valid_ndfd_elements = ('maxt', 'mint', 'temp', 'dew', 'appt',
        'pop12', 'qpf', 'snow', 'sky', 'rh', 'wspd', 'wdir', 'wx', 'icons',
        'waveh', 'incw34', 'incw50', 'incw64', 'cumw34', 'cumw50',
        'cumw64', 'wgust', 'critfireo', 'dryfireo', 'conhazo', 'ptornado',
        'phail', 'ptstmwinds', 'pxtornado', 'pxhail', 'pxtstmwinds',
        'ptotsvrtstm', 'pxtotsvrtstm', 'tmpabv14d', 'tmpblw14d',
        'tmpabv30d', 'tmpblw30d', 'tmpabv90d', 'tmpblw90d', 'prcpabv14d',
        'prcpblw14d', 'prcpabv30d', 'prcpblw30d', 'prcpabv90d',
        'prcpblw90d', 'precipa_r', 'sky_r', 'td_r', 'temp_r', 'wdir_r',
        'wspd_r', 'wwa', 'iceaccum', 'maxrh', 'minrh')

    def __init__(self, list_lat_lon='', product='glance', begin=None, end=None, unit=None, ndfd_elements=()):
        self.list_lat_lon = list_lat_lon
        self.product = product
        self.begin = begin
        self.end = end
        self.unit = unit
        self.ndfd_elements = ndfd_elements
        self.__response = None

    @property
    def list_lat_lon(self):
        return self.__list_lat_lon

    @list_lat_lon.setter
    def list_lat_lon(self, coords):
        if coords == '' or re.match(r'^(-?\d{1,3}(\.\d*)?,-?\d{1,3}(\.\d*)? ){0,199}-?\d{1,3}(\.\d*)?,-?\d{1,3}(\.\d*)?$', coords):
            self.__list_lat_lon = coords
        else:
            raise ValueError("The 'listLatLon' string is not properly formatted.")

    def add_lat_lon_coords(self, coords):
        """
        Adds latitude,longitude coordinates to the list_lat_lon attribute.

        Args:
            coords (str): A properly formatted string of coordinates.
                (eg: '40.71,-74.01 34.05,-118.25')
        """

        if not self.list_lat_lon:
            self.list_lat_lon = coords
        else:
            self.list_lat_lon = self.list_lat_lon + ' ' + coords

    def import_list_lat_lon_from_csv(self, csvfilepath):
        """
        Imports latitude,longitude coordinates from a csv file. Overrides any
        existing coordinates. The csv file must include a column with header
        "Latitude" and another column with header "Longitude". Values in these
        two columns must be individual numbers.

        Args:
            csvfilepath (str): The full or relative filepath of the csv file.
                (eg: "C:\\Users\\user\\Documents\\MyCoords.csv"
                or "./MyProject/LatLongs.csv")
        """

        lat_longs = []
        with open(csvfilepath, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile, skipinitialspace=True)
            for row in csvreader:
                lat_longs.append(row['Latitude'] + ',' + row['Longitude'])
        self.list_lat_lon = ' '.join(lat_longs)

    @property
    def product(self):
        return self.__product

    @product.setter
    def product(self, text):
        if text in ('time-series', 'glance'):
            self.__product = text
        else:
            raise ValueError("The value of 'product' must be 'time-series' or 'glance'.")

    @property
    def begin(self):
        return self.__begin

    @begin.setter
    def begin(self, begin_time):
        if isinstance(begin_time, datetime.datetime) or begin_time is None:
            self.__begin = begin_time
        else:
            raise ValueError("The value of 'begin' must be of type datetime.datetime or None.")

    @property
    def end(self):
        return self.__end

    @end.setter
    def end(self, end_time):
        if isinstance(end_time, datetime.datetime) or end_time is None:
            self.__end = end_time
        else:
            raise ValueError("The value of 'end' must be of type datetime.datetime or None.")

    @property
    def unit(self):
        return self.__unit

    @unit.setter
    def unit(self, text):
        if text in ('e', 'm') or text is None:
            self.__unit = text
        else:
            raise ValueError("The value of 'Unit' must be 'e', 'm', or None.")

    @property
    def ndfd_elements(self):
        return self.__ndfd_elements

    @ndfd_elements.setter
    def ndfd_elements(self, elements):
        if not isinstance(elements, (tuple, list)):
            raise TypeError("The attribute 'ndfd_elements' must be set as a tuple or a list.")
        for element in elements:
            if element not in self.__valid_ndfd_elements:
                raise ValueError(f"'{element}' is not a valid NDFD element.")
        self.__ndfd_elements = tuple(dict.fromkeys(elements))

    def add_ndfd_elements(self, *elements):
        """Adds one or more NDFD elements to the query list."""
        self.ndfd_elements = self.ndfd_elements + tuple(elements)

    def remove_ndfd_elements(self, *elements):
        """Removes one or more NDFD elements from the query list."""
        self.ndfd_elements = tuple(filter(lambda ndfd_element: ndfd_element not in elements, self.ndfd_elements))

    def __create_payload(self):
        payload = {'listLatLon': self.list_lat_lon, 'product': self.product}
        if self.begin:
            payload.update({'begin': self.begin.isoformat()})
        if self.end:
            payload.update({'end': self.end.isoformat()})
        if self.unit:
            payload.update({'Unit': self.unit})
        if self.product == 'time-series':
            for element in self.ndfd_elements:
                payload.update({element: element})
        return payload

    def __str__(self):
        return str(self.__create_payload())

    def send_query(self):
        """
        Builds the query url and sends an HttpRequest to the NDFD REST API.
        Expects an xml document in response.

        Raises:
            ValueError: If list_lat_lon has no coordinates.
            ValueError: If ndfd_elements has no elements
                while product is time-series.
        """

        if not self.list_lat_lon:
            raise ValueError("The attribute 'list_lat_lon' must have coordinates.")
        if self.product == 'time-series' and not self.ndfd_elements:
            raise ValueError("While 'product' is 'time-series', the attribute 'ndfd_elements' must have at least one element.")
        self.__response = requests.get('https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php', params=self.__create_payload())

    def get_response(self):
        """
        Returns the entire response object that was recieved
        from the NDFD REST API, or returns None if there is no response,
        which may mean that send_query() has not yet been called.
        """

        return self.__response

    def __create_filename(self, extention):
        soup = BeautifulSoup(self.__response.text, 'lxml')
        creation_date = soup.find('creation-date')
        if creation_date:
            return ''.join([char for char in creation_date.text if char.isdigit()]) + '_t' + extention
        return 'ERROR' + extention

    def save_xml(self, filepath=''):
        """
        Saves to disk the xml file recieved in the response
        from the NDFD REST API. Returns 0 if there is no response,
        which may mean that send_query() has not yet been called.

        Args:
            filepath (str, optional): The full or relative filepath of the
                xml file to be saved. Defaults based on creation-date to
                'yyyymmddhhmmss_t.xml' or 'ERROR.xml'.
        """

        if not self.__response:
            return 0

        if filepath == '' or filepath[-1] in '\\/':
            filepath = filepath + self.__create_filename('.xml')
        elif len(filepath) < 4 or filepath[-4:] != '.xml':
            filepath = filepath + '.xml'

        i = 1
        while os.path.exists(filepath):
            if not re.match(r'.*\(\d+\)\.xml$', filepath):
                filepath = filepath[:-4] + '(' + str(i) + ').xml'
            else:
                filepath = filepath[:-6] + str(i) + ').xml'
                i += 1

        with open(filepath, 'w') as xmlfile:
            xmlfile.write(self.__response.text)
