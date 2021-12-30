import pandas as pd
import logging

from RPA.Browser.Selenium import Selenium
from RPA.PDF import PDF
from robot.libraries.String import String

from time import sleep

from pathlib import Path
from config.common import config

from openpyxl import load_workbook

pdf_path = Path(config()['pdf_path']) 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


browser_lib = Selenium()

logger.info('Set download directory')
browser_lib.set_download_directory(directory=pdf_path.resolve(), download_pdf=True)

pdf = PDF()
string = String()


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
    logger.info(f'Diving through agency {agency_name}')

    data = browser_lib.get_webelements('//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')

    for elem in data: 
        if elem.text == agency_name:
            agency = elem

    browser_lib.click_element_when_visible(agency)


def get_full_table():
    logger.info('Extract table from selected agency')

    select_field = '//select[@name="investments-table-object_length"]/option[text()="All"]'
    browser_lib.click_element_when_visible(select_field)

    sleep(10)

    headers = browser_lib.get_webelements('//div[@class="dataTables_scrollHeadInner"]/table/thead/tr/th')
    headers = [x.text for x in headers]

    table = browser_lib.get_webelements('//div[@class="dataTables_scrollBody"]/table/tbody/tr/td')
    table = [x.text for x in table]
    
    data = [table[i:i + len(headers)] for i in range(0, len(table), len(headers))]

    df = pd.DataFrame(data, columns=headers)

    return df


def save_table(df, filename, sheet_name):
    logger.info(f'Append agency table into excel file at {filename}')

    with pd.ExcelWriter(filename, mode='a') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0, startcol=0)


def download_pdfs():

    logger.info('Download pdfs')

    links = browser_lib.get_webelements('//div[@class="dataTables_scrollBody"]/table/tbody/tr/td/a')
    links = [x.text for x in links]

    main_url = browser_lib.get_location()

    for link in links:
#        print('')
#        print(main_url)
#        print(link)
#        print(main_url+'/'+link)
#        print('')
        browser_lib.go_to(main_url+'/'+link)
        pdf_download_link = '//div[@id="business-case-pdf"]/a'
        browser_lib.wait_until_element_is_enabled(pdf_download_link, 10, 'Element not visible')
        browser_lib.click_element_when_visible(pdf_download_link)

        download_span = '//div[@id="business-case-pdf"]/span'
        try:
            browser_lib.wait_until_element_is_visible(download_span, 20)
            browser_lib.wait_until_element_is_not_visible(download_span, 20)
        except AssertionError as error:
            print(error)


def extract_data_from_pdf(pdf_path):
    logger.info('Extract the data from the PDFs using regex')
    data = {}

    text = pdf.get_text_from_pdf(pdf_path, pages=[1])
    investment_name = string.get_regexp_matches(text[1], '(?<=Name of this Investment: )(.*)(?=2. Unique Investment Identifier)')
    uii = string.get_regexp_matches(text[1], '(?<=Unique Investment Identifier \(UII\): )(.*)(?=Section B)')

    data['uii'] = uii[0]
    data['investment_name'] = investment_name[0]
    
    return data


def compare_pdf_with_excel(filename, data):
    logger.info('Add a column to the excel file with the Titles from the PDFs, comparing UII')
    df = pd.read_excel(filename, sheet_name=config()['agency'][0:30])
    
    new_column = []
    for elem in df['UII']:
        if elem in data:
            new_column.append(data[elem])
        else:
            new_column.append('Not in PDF')

    df['Title in PDF'] = new_column

    return df


def save_updated_df(df, filename, sheet_name):
    # df.to_excel(filename, sheet_name=config()['agency'], index=False)
    logger.info('Update dataframe with new column')

    excel_book = load_workbook(filename)

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
    
        writer.book = excel_book
        writer.sheets = dict((ws.title, ws) for ws in excel_book.worksheets)

        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0, startcol=0)

        writer.save()

# Define a main() function that calls the other functions in order:
def main():
    
    # Scrape data from web 
    try:
        open_the_website("https://itdashboard.gov/")
        click_dive_in()
        sleep(2)
        data_tuples = get_data()
        sleep(2)
        df = creating_dataframe(data_tuples)

        saving_excel(df, 'output/output.xlsx')

        agency = config()['agency']
        dive_through_agency(agency) 
        sleep(5)

        df = get_full_table()

        save_table(df, 'output/output.xlsx', agency[0:30])

        sleep(5)

        download_pdfs()

        sleep(5)

    finally:
        browser_lib.close_all_browsers()


    # Compare data in excel with PDFs
    data = {}

    for current_file in pdf_path.iterdir():
        raw = extract_data_from_pdf(current_file)

        data[raw['uii']] = raw['investment_name']

    df = compare_pdf_with_excel('./output/output.xlsx', data)
    save_updated_df(df, './output/output.xlsx', agency[0:30])

    pdf.close_all_pdfs()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
