import requests
#   TQDM to have a fancy loading bar (for loading ~3500 pages of potential data)
from tqdm import tqdm


#   For determining what data to store
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


class CarZoneParser:
    #   Constructor with base_url setter
    def __init__(self, url: str):
        self.base_url = url
        self.page_ext = '?page='

    #   Method for parsing response data

    #   Return the page count according to base_url
    def __get_page_count(self) -> int:
        return requests.get(self.base_url).json()['totalPages']

    def get_pages_data(self, page_count: int) -> list:
        page_max = self.__get_page_count()
        if page_count <= 0 or page_count > page_max:
            page_count = page_max
        info_list = []
        for i in tqdm(range(1, page_count + 1), desc='Loading pages'):
            items = requests.get(self.base_url + self.page_ext + str(i)).json()['results'][1]['items']
            for j in range(len(items)):
                info_list.append(parse_json_item(items[j]['summary']))
        return info_list
