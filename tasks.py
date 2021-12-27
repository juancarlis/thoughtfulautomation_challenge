from RPA.Browser.Selenium import Selenium
from time import sleep

import pandas as pd

browser_lib = Selenium()


def open_the_website(url):
    browser_lib.open_available_browser(url)


def click_dive_in():
    button_xpath = '//*[@id="node-23"]/div/div/div/div/div/div/div/a'
    browser_lib.click_element_when_visible(button_xpath)


def get_data():
    data = browser_lib.get_webelements('//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')
    data = [x.text for x in data]

    agencies = [ele for idx, ele in enumerate(data) if idx % 2 != 0]
    amount = [ele for idx, ele in enumerate(data) if idx % 2 == 0]

    data_tuples = list(zip(agencies, amount))

    return data_tuples


def creating_dataframe(data_tuples):
    df = pd.DataFrame(data_tuples, columns=['Agencies', 'Amount'])

    return df

# Define a main() function that calls the other functions in order:
def main():
    try:
        open_the_website("https://itdashboard.gov/")
        click_dive_in()
        data_tuples = get_data()
        print(data_tuples)
        creating_dataframe(data_tuples)
    finally:
        browser_lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
