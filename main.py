import async_parser
import carzone_parser
import pandas as pd


#   First method for retrieving all the data (slow)
#   ran for 20+ min for 3500 results (~3 results per sec)
def get_data():
    car_parser = carzone_parser.CarZoneParser('https://www.carzone.ie/rest/1.0/Car/stock')
    data = car_parser.get_pages_data(-1)
    for i in data:
        print(i)

    df = pd.DataFrame(data)
    df.to_csv(r'test1.csv', index=False, header=True)


#   Improvement upon original parser using async functionality to significantly speed up the process
#   Ran for 5 min for 3500 results (~12 results per sec) less that theoretically expected
#   chunk_size = 10, timeout = 0.5
############################
#   extras parameter queries information that otherwise is not easily visible. This increases the request count
# ~10 times. With this increase I added retries to each request to help mitigate the amount of 429 errors. After max
# retires fail the data is dropped.
#   Relying fully on retry_timeout and max_retries compared to timeout seems reliably faster. Chunk_size=4 works too.
#   100 pages load reliably under 1 min, 400 under 4  minutes. Seems linear.
def get_async_data():
    #   chunk_size = 10 and timeout=0.5 provides enough timeout to avoid 429 (too many requests)
    scrapper = async_parser.Scraper(
        chunk_size=4,
        timeout=0,
        page_count=400,
        extras=True,
        max_retries=5,
        retry_timeout=0.5,
    )
    #   Print details of execution
    scrapper.info()
    scrapper.get_errors()
    #   Save details into a file
    df = pd.DataFrame(scrapper.results)
    df.to_csv(r'carzone_results.csv', index=False, header=True)


if __name__ == '__main__':
    get_async_data()
