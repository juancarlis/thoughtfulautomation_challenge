# RPA
from RPA.Browser.Selenium import Selenium
from RPA.PDF import PDF
from robot.libraries.String import String

# Helpers
import logging
import pandas as pd

from time import sleep
from config.common import config
from pathlib import Path


# Globals

# Path where the pdf files are downloaded
pdf_path = Path(config()['pdf_path'])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Browser object
browser_lib = Selenium()

# Set browser download directory
logger.info('Set download directory')
browser_lib.set_download_directory(
    directory=pdf_path.resolve(), download_pdf=True)

# PDF object
pdf = PDF()
string = String()


def open_the_website(url):
    """Open website"""

    logger.info(f'Open website: {url}')
    browser_lib.open_available_browser(url)


def click_dive_in():
    """Click the 'Dive In' button"""

    logger.info('Click dive in button')
    button_xpath = '//*[@id="node-23"]/div/div/div/div/div/div/div/a'
    browser_lib.click_element_when_visible(button_xpath)


def get_agencies_amount():
    """Scrape for each agency and the corresponding amount and
    returns a dataframe with two columns:
        - Agencies
        - Amounts

    Returns:
        df (df): dataframe with two columns ['Agencies', 'Amounts']

    """

    # Get every agency name and amount by xpath and transform it into
    # a list of elements
    logger.info('Access all agencies by xpath')
    data = browser_lib.get_webelements(
        '//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')
    data = [x.text for x in data]

    # Split the data in the format:
    # ['Agency_1', 'Amount_1', 'Agency_2', 'Amount_2', ...]
    # into two separates lists, one for the agencies
    # and the other for the amounts

    logger.info('Split data into agencies and amounts')
    agencies = [ele for idx, ele in enumerate(data) if idx % 2 != 0]
    amounts = [ele for idx, ele in enumerate(data) if idx % 2 == 0]

    # Create list of tuples in the format:
    # [('Agency_1', 'Amount_1'), ('Agency_2', 'Amount_2'), ...]
    agency_amount_tuples = list(zip(amounts, agencies))

    # Creates a dataframe with the tuples from the previous step
    logger.info('Create dataframe from data tuples')
    df_agencies = pd.DataFrame(
        agency_amount_tuples,
        columns=['Agencies', 'Amounts']
    )

    return df_agencies


def _save_df_to_excel(df, filename, sheet_name, append=False):
    """
    Saves a given dataframe to an xlsx file.

    Parameters:

        df (df): dataframe with agencies and amounts
        filename (str): path and name of the excel file
    """

    logger.info(f'Saving into excel file at {filename}')

    if not append:
        df.to_excel(
            filename,
            sheet_name=sheet_name,
            index=False,
            startrow=0,
            startcol=0
        )
    else:
        with pd.ExcelWriter(filename, mode='a') as writer:
            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
                startrow=0,
                startcol=0
            )


def dive_through_agency(agency_name):
    """
    Finds the agency name given and click on its web element
    """
    logger.info(f'Diving through agency {agency_name}')

    # Store every agency web element in agencies variable
    # then loop through each agency web element and if it
    # finds a match with agency_name then click on it
    agencies = browser_lib.get_webelements(
        '//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')

    agency_element = None

    for agency in agencies:
        if agency.text == agency_name:
            agency_element = agency

    if agency_element is not None:
        browser_lib.click_element_when_visible(agency_element)
    else:
        logger.info('The Agency does not exist!')
        browser_lib.close_all_browsers()
        exit()


def get_individual_investments_table():
    """
    Gets the table with all 'Individual Investments' and returns a dataframe
    with the data.

    Returns:
        df_individual_investments (df): dataframe containing the data extracted
                                        from the web.
    """
    logger.info(
        'Extracting table with the "Individual Investments" from chosen agency')

    # To make the table show the whole content
    select_field = '//select[@name="investments-table-object_length"]/option[text()="All"]'
    browser_lib.click_element_when_visible(select_field)

    sleep(10)

    # Get the table headers
    headers = browser_lib.get_webelements(
        '//div[@class="dataTables_scrollHeadInner"]/table/thead/tr/th')
    headers = [x.text for x in headers]

    # Get the table in raw data format, as a list of elements with no
    # differentiating into rows or columns.
    raw_data = browser_lib.get_webelements(
        '//div[@class="dataTables_scrollBody"]/table/tbody/tr/td')
    raw_data = [data.text for data in raw_data]

    # Transform the raw data into a list of lists, where the sublists
    # represents each row of the table.
    data = [raw_data[i:i + len(headers)]
            for i in range(0, len(raw_data), len(headers))]

    # Create a dataframe with the data and the headers
    df_individual_investments = pd.DataFrame(data, columns=headers)

    return df_individual_investments


def download_pdfs():

    logger.info('Download pdfs')

    links = browser_lib.get_webelements(
        '//div[@class="dataTables_scrollBody"]/table/tbody/tr/td/a')
    links = [x.text for x in links]

    main_url = browser_lib.get_location()

    for link in links:
        browser_lib.go_to(main_url+'/'+link)
        pdf_download_link = '//div[@id="business-case-pdf"]/a'
        browser_lib.wait_until_element_is_enabled(
            pdf_download_link, 10, 'Element not visible')
        browser_lib.click_element_when_visible(pdf_download_link)

        download_span = '//div[@id="business-case-pdf"]/span'
        try:
            browser_lib.wait_until_element_is_visible(download_span, 20)
            browser_lib.wait_until_element_is_not_visible(download_span, 20)
        except AssertionError as error:
            print(error)


def extract_data_from_pdf(pdf_path):
    logger.info(
        f'Extract the data from the PDFs using regex at path: {pdf_path}')
    data = {}

    text = pdf.get_text_from_pdf(pdf_path, pages=[1])
    investment_name = string.get_regexp_matches(
        text[1], '(?<=Name of this Investment: )(.*)(?=2. Unique Investment Identifier)')
    uii = string.get_regexp_matches(
        text[1], '(?<=Unique Investment Identifier \(UII\): )(.*)(?=Section B)')

    data['uii'] = uii[0]
    data['investment_name'] = investment_name[0]

    return data


def compare_pdf_with_excel(filename, data):
    logger.info(
        'Add a column to the excel file with the Titles from the PDFs, comparing UII')
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

    with pd.ExcelWriter(filename, mode='a') as writer:
        df.to_excel(writer, sheet_name=sheet_name,
                    index=False, startrow=0, startcol=0)

# Define a main() function that calls the other functions in order:


def main():

    # Scrape data from website: 'https://itdashboard.gov/'
    try:
        # Extractig excel file with agencies and amounts
        open_the_website("https://itdashboard.gov/")
        click_dive_in()
        sleep(2)
        df_agencies_amount = get_agencies_amount()
        sleep(2)

        _save_df_to_excel(
            df_agencies_amount,
            'output/output.xlsx',
            'Agencies',
            append=False
        )

        # Scraping through the agency determined in the config file
        agency = config()['agency']
        dive_through_agency(agency)
        sleep(5)

        df_individual_investments_table = get_individual_investments_table()
#        save_table(df, 'output/output.xlsx', agency[0:30])
        _save_df_to_excel(
            df_individual_investments_table,
            'output/output.xlsx',
            agency[0:30],
            append=True
        )
#
#        sleep(5)
#
#        download_pdfs()
#
#        sleep(5)
#
    finally:
        browser_lib.close_all_browsers()
#
#    # Compare data in excel with PDFs
#    data = {}
#
#    for current_file in pdf_path.iterdir():
#        if str(current_file)[-4:] == '.pdf':
#            raw = extract_data_from_pdf(current_file)
#
#            data[raw['uii']] = raw['investment_name']
#
#    df = compare_pdf_with_excel('./output/output.xlsx', data)
#    save_updated_df(df, './output/output.xlsx', 'PDF comparison')
#
#    pdf.close_all_pdfs()


# Call the main() function,
# checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
