import asyncio

import requests

import async_parser
import carzone_parser
import pandas as pd

# print(requests.get('https://www.carzone.ie/rest/1.0/Car/stock?page=1').json())

# car_parser = carzone_parser.CarZoneParser('https://www.carzone.ie/rest/1.0/Car/stock')
#
# data = car_parser.get_pages_data(-1)
# for i in data:
#     print(i)
#
# df = pd.DataFrame.from_dict(data)
# df.to_csv(r'test1.csv', index=False, header=True)


var = async_parser.Scraper('https://www.carzone.ie/rest/1.0/Car/stock?page=', 500)
