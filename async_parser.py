import asyncio
import aiohttp
from tqdm import tqdm


def parse_json_item(json_dict: dict) -> dict:
    """
    Parses json file for details (format as per sample_summary.json). \

    :param json_dict: json extract to be parsed
    :return: Returns a dict with specified values:
    public_reference, price_euro, engine_size, engine_size_cc, fuel_type, transmission, mileage_km, colour, make, model,
    registration_year, sale_city, sale_county
    """
    car_info = dict()
    car_info['public_reference'] = json_dict['publicReference']
    car_info['price_euro'] = json_dict['sale']['advertPricing']['euroPrice']
    car_info['engine_size'] = json_dict['engineSize']
    car_info['engine_size_cc'] = json_dict['engineSizeCC']
    car_info['fuel_type'] = json_dict['searchDetailSummary']['fuelType']
    car_info['transmission'] = json_dict['searchDetailSummary']['transmission']
    car_info['mileage_km'] = int(json_dict['vehicle']['mileage']['mileageKm'] or 0)
    car_info['colour'] = json_dict['vehicle']['colour']
    car_info['make'] = json_dict['searchDetailSummary']['mmv']['make']
    car_info['model'] = json_dict['searchDetailSummary']['mmv']['model']
    car_info['registration_year'] = json_dict['vehicle']['registrationYear']
    car_info['sale_city'] = json_dict['stockLocation']['city']
    car_info['sale_county'] = json_dict['stockLocation']['county']
    return car_info


def append_item_extra(base_dict: dict, extra_info: dict) -> dict:
    """
    Parses json file for details and appends them to given dict.
    Not all values will be assigned.\

    :param base_dict: base dict to be appended to
    :param extra_info: json dict with data for appending (as per sample_extra.json)
    :return: Returns a dict with additional values:
    seller_type, nct, tax, seats, doors, body_type, owners, condition, registration
    """
    base_dict['seller_type'] = extra_info['advertiser']['sellerType'] or ''
    base_dict['nct'] = extra_info['vehicle']['motDate'] or ''
    base_dict['tax'] = extra_info['vehicle']['taxBand'] or ''
    base_dict['seats'] = extra_info['specification']['seats'] or ''
    base_dict['doors'] = extra_info['specification']['doors'] or ''
    base_dict['body_type'] = extra_info['specification']['bodyType'] or ''
    base_dict['owners'] = extra_info['vehicle']['owners'] or ''
    base_dict['condition'] = extra_info['vehicle']['condition'] or ''
    base_dict['registration'] = extra_info['vehicle']['registration'] or ''
    return base_dict


class Scraper(object):
    def __init__(self, page_count=0, chunk_size=10, timeout=float(1), extras=False, retry_timeout=1, max_retries=3):
        #   base url to be used for requests
        self.url = "https://www.carzone.ie/rest/1.0/Car/stock?page="
        #   eg: https://www.carzone.ie/rest/1.0/Car/fpa/202209099592611?journey=Search
        #   designed to be used with .format
        self.fpa = "https://www.carzone.ie/rest/1.0/Car/fpa/{0:s}?journey=Search"
        # print(self.fpa.format(2222))

        #   variables to be used in automatic retires (to help prevent occasional 429-too_many_requests denis)
        self.retry_timeout = retry_timeout
        self.max_retries = max_retries

        self.extras = extras
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.page_count = page_count
        self.expected_items = page_count * 10
        self.pages_requested = 0
        self.timeout_count = [0] * self.max_retries
        self.errors_encountered = []
        #   Check if page_count specified, if not default to available page_count
        if page_count <= 0:
            self.page_count, self.expected_items = asyncio.run(self.get_properties())
        self.results = asyncio.run(self.main())

    #   Tiny method to return totalPages and totalResults for later comparisons
    async def get_properties(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                json = await response.json()
                return json['totalPages'], json['totalResults']

    #   Fetch single page of items
    async def fetch(self, session, num: int) -> list:
        try:
            # A rudimentary implementation of automated retries (in case of 429 responses)
            for i in range(self.max_retries):
                async with session.get(self.url + str(num)) as response:
                    #   If 200 process given json
                    if response.status == 200:
                        #   Wait for the response and parse
                        json = await response.json()
                        #   Target items
                        items = json['results'][1]['items']
                        #   Loop through all, add together and return
                        car_list = []
                        #   Loop through all items in the page
                        for j in range(len(items)):
                            car_details = parse_json_item(items[j]['summary'])
                            #   if extras query and append info
                            if self.extras:
                                extra_info = await self.get_details(session, car_details['public_reference'])
                                if extra_info is not None:
                                    append_item_extra(car_details, extra_info)
                                    car_list.append(car_details)
                            else:
                                car_list.append(car_details)
                        return car_list
                    else:
                        await asyncio.sleep(self.retry_timeout)
                self.timeout_count[i] += 1
            #   throw exception after max_retires
            raise Exception(f"Response code: {response.status}, could not retrieve url='{self.url + str(num)}'")
        except Exception as e:
            #   Save error and return empty list (no return may break methods that use this)
            self.errors_encountered.append(e)
            return []

    async def get_details(self, session, pref: int) -> dict | None:
        try:
            for i in range(self.max_retries):
                async with session.get(self.fpa.format(pref)) as response:
                    if response.status == 200:
                        json = await response.json()
                        return json['fpa']
                    else:
                        await asyncio.sleep(self.retry_timeout)
                self.timeout_count[i] += 1
            raise Exception(f"Response code: {response.status}, could not retrieve url='{self.fpa.format(pref)}'")
        except Exception as e:
            self.errors_encountered.append(e)
            return None

    #   main function to be run upon creation
    async def main(self):
        results = []
        tasks = []
        async with aiohttp.ClientSession() as session:
            #   Loop for page_count and utilize tqdm to provide progress feedback
            for i in tqdm(range(self.page_count)):
                tasks.append(self.fetch(session, i))
                self.pages_requested += 1
                #   Break up massive task (chunks of 10) and sleep
                #   Prevents being blocked due to too many requests
                if i % self.chunk_size == 0:
                    results += await asyncio.gather(*tasks)
                    tasks = []
                    await asyncio.sleep(self.timeout)
            #   Check if there were any leftover tasks after the loop (for unequal divisions)
            if len(tasks) > 0:
                results += await asyncio.gather(*tasks)

        #   Merge lists into one and return
        final_list = []
        for test in results:
            final_list += test
        return final_list

    def info(self):
        print(f"Base url used='{self.url}'")
        print(f"Extras mode = {self.extras}")
        print(f"Times timed out = {self.timeout_count}")
        print(f"Errors encountered = {len(self.errors_encountered)}")
        print(f"Pages expected = {self.page_count}, requested = {self.pages_requested}")
        print(f"Items expected = {self.expected_items}, received = {len(self.results)}")

    def get_errors(self):
        for i in self.errors_encountered:
            print(i)
