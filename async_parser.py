import asyncio
import aiohttp


def parse_json_item(json_dict: dict) -> dict:
    car_info = dict()
    car_info['publicReference'] = json_dict['publicReference']
    car_info['price'] = json_dict['sale']['advertPricing']['price']
    car_info['price_unit'] = json_dict['sale']['advertPricing']['unit']
    car_info['price_vat'] = json_dict['priceDetail']['vatIncluded']
    car_info['engineSize'] = json_dict['engineSize']
    car_info['engineSizeCC'] = json_dict['engineSizeCC']
    car_info['registrationYear'] = json_dict['vehicle']['registrationYear']
    car_info['colour'] = json_dict['vehicle']['colour']
    car_info['mileageKm'] = json_dict['vehicle']['mileage']['mileageKm']
    car_info['make'] = json_dict['searchDetailSummary']['mmv']['make']
    car_info['model'] = json_dict['searchDetailSummary']['mmv']['model']
    car_info['fuelType'] = json_dict['searchDetailSummary']['fuelType']
    car_info['transmission'] = json_dict['searchDetailSummary']['transmission']
    car_info['sale_city'] = json_dict['stockLocation']['city']
    car_info['sale_county'] = json_dict['stockLocation']['county']
    return car_info


class Scraper(object):
    def __init__(self, url: str, page_count: int):
        self.page_count = page_count
        self.url = url
        # self.all_list = []
        # self.master_dict = {}
        asyncio.run(self.main())

    #   Fetch single page of items
    async def fetch(self, session, num: int) -> list:
        try:
            async with session.get(self.url + str(num)) as response:
                json = await response.json()
                items = json['results'][1]['items']
                car_list = []
                for i in range(len(items)):
                    car_list.append(parse_json_item(items[i]['summary']))
                return car_list
        except Exception as e:
            print('Error: ' + str(e))

    #
    async def main(self):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(self.page_count):
                tasks.append(self.fetch(session, i))

            results = await asyncio.gather(*tasks)

        for test in results:
            print(test)

