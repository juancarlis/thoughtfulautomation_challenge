from RPA.Browser.Selenium import Selenium
from time import sleep

import pandas as pd
import logging

from config.common import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


browser_lib = Selenium()


def open_the_website(url):
    logger.info(f'Open website: {url}')
    browser_lib.open_available_browser(url)


def click_dive_in():
    logger.info('Click dive in button')
    button_xpath = '//*[@id="node-23"]/div/div/div/div/div/div/div/a'
    browser_lib.click_element_when_visible(button_xpath)


def get_data():
    logger.info('Access all agencies by xpath')
    data = browser_lib.get_webelements('//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')
    data = [x.text for x in data]

    logger.info('Clean data and return into list of tuples')
    agencies = [ele for idx, ele in enumerate(data) if idx % 2 != 0]
    amount = [ele for idx, ele in enumerate(data) if idx % 2 == 0]

    data_tuples = list(zip(amount, agencies))

    return data_tuples


def creating_dataframe(data_tuples):
    logger.info('Create dataframe from data tuples')
    df = pd.DataFrame(data_tuples, columns=['Agencies', 'Amount'])

    return df


def saving_excel(df, filename):
    logger.info(f'Save into excel file at {filename}')

    df.to_excel(filename, sheet_name='Agencies', index=False, startrow=0, startcol=0)


def dive_through_agency(agency_name):

    data = browser_lib.get_webelements('//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')

    for elem in data: 
        if elem.text == agency_name:
            agency = elem

    browser_lib.click_element_when_visible(agency)


def get_full_table():

    select_field = '//select[@name="investments-table-object_length"]/option[text()="All"]'
    browser_lib.click_element_when_visible(select_field)


# Define a main() function that calls the other functions in order:
def main():
    try:
        open_the_website("https://itdashboard.gov/")
        click_dive_in()
        sleep(2)
        data_tuples = get_data()
        sleep(2)
        df = creating_dataframe(data_tuples)

        saving_excel(df, 'output/agencies.xlsx')

        agency = config()['agency']
        dive_through_agency(agency) 
        sleep(5)

        get_full_table()
        sleep(5)

    finally:
        browser_lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
