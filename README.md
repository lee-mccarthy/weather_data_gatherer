# weather_data_gatherer

A tool for gathering weather forecast data from the [NDFD REST API](https://graphical.weather.gov/xml/rest.php).

The file 'ndfd_xml_client.py' is for general use, but the rest of this repo was  
made for a specific client. Logan McCarthy uses this repo to gather data for  
a weather report segment that he does at the beginning of his streams. You can  
watch him on [YouTube](https://www.youtube.com/user/Paradoxwidget), [Twitch](https://www.twitch.tv/longhairlogan), and [Facebook](https://www.facebook.com/LoganMcCarthySadLogos).

## Table of Contents

- Main Components
    - ndfd_xml_client.py
    - main<span>.</span>py
- Sample Files
    - program_data/cities.csv
    - program_data/linebreaks.txt
- Web Scrapers
    - scrapers/wiki_scraper.ipynb
    - scrapers/ndfd_elements_scraper.ipynb

## Main Components

### ndfd_xml_client.py

Includes a class called `MPUD` (an acronym for Multiple Point Unsummarized  
Data) that interacts with the NDFD REST API. Information about this API can  
be found at <https://graphical.weather.gov/xml/rest.php>, and valid query  
elements can be found at  
<https://graphical.weather.gov/xml/docs/elementInputNames.php>.

It is recommended to use this class in the following manner:

1. Construct a weather data query at object initialization or using the various  
methods.
2. Send the query to the NDFD REST API using `send_query()`.
3. Save a copy of the xml file returned from the API using `save_xml()`.

### main<span>.</span>py

This file was written for a very specific use case. It uses the `MPUD` class  
from 'ndfd_xml_client.py' to query the NDFD REST API for tomorrow's "maxt"  
values in various locations defined in 'program_data/cities.csv'. The xml file  
is saved in 'program_data/xml/', and a .txt file containing parsed and  
formatted data is saved in 'weather_reports/'.

A file called 'last_query_time.txt' is saved in 'program_data/'. This file is  
referenced by 'main<span>.</span>py' to put itself on a one-hour cooldown timer  
after a successful query.

## Sample Files

### program_data/cities.csv

The file 'main<span>.</span>py' references this file to load latitude and  
longitude coordinates into it's query, and to include location names in the  
formatted output. This file can be modified to remove locations or include new  
ones.

### program_data/linebreaks.txt

The file 'main<span>.</span>py' references this file if it exists to include  
linebreaks after specified locations in the formatted output. This file can be  
modified to change where linebreaks occur, or it can be deleted entirely.

## Web Scrapers

### scrapers/wiki_scraper.ipynb

This jupyter notebook was used to gather latitude and longitude coordinates  
from Wikipedia for the cities the client specified. The file  
'program_data/cities.csv' as it is in this repo was built using this scraper.

### scrapers/ndfd_elements_scraper.ipynb

This jupyter notebook was used to construct a tuple of valid NDFD elements from  
<https://graphical.weather.gov/xml/docs/elementInputNames.php>. The tuple is  
included in the `MPUD` class definition in the file 'ndfd_xml_client.py' to  
validate user input.
