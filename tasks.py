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
    button_xpath = '//a[@href="#home-dive-in"]'
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
        '//div[@class="col-sm-4 text-center noUnderline"]//span')
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
        sheet_name (str): sheet where the dataframe is pasted
        append (bool): if False creates a new excel file
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
        '//div[@class="col-sm-4 text-center noUnderline"]//span')

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
        'Extracting table with the "Individual Investments" from chosen agency'
    )

    # Write "All" in the select field to make the table shows the full content
    select = '//select[@name="investments-table-object_length"]/option[text()="All"]'
    browser_lib.click_element_when_visible(select)

    sleep(10)

    # Get the table headers
    headers = browser_lib.get_webelements(
        '//div[@class="dataTables_scrollHeadInner"]//th')
    headers = [x.text for x in headers]

    # Get the table in raw data format, as a list of elements with no
    # differentiating into rows or columns.
    raw_data = browser_lib.get_webelements(
        '//div[@class="dataTables_scrollBody"]//tbody//td')
    raw_data = [data.text for data in raw_data]

    # Transform the raw data into a list of lists, where the sublists
    # represents each row of the table.
    data = [raw_data[i:i + len(headers)]
            for i in range(0, len(raw_data), len(headers))]

    # Create a dataframe with the data and the headers
    df_individual_investments = pd.DataFrame(data, columns=headers)

    return df_individual_investments


def download_pdfs():
    """
    Downloads the PDF files of the chosen agency by pressing on the button:
     - Download Business Case PDF
    """

    logger.info('Downloading chosen agency PDFs')

    # Get every link in a list of web elements and converted to strings
    links = browser_lib.get_webelements(
        '//div[@class="dataTables_scrollBody"]//a')
    links = [x.text for x in links]

    # Store the main URL of the agency
    # For example: https://itdashboard.gov/drupal/summary/005
    main_url = browser_lib.get_location()

    # Loop through the list of links and gets the endpoint of each UII
    # with a PDF file
    # In the example:
    # 'https://itdashboard.gov/drupal/summary/005' + '/' + 'link'
    # Then the scraper goes to each link and presses the download button
    # when its visible
    # The download path is set in the globals and defined by the config file

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
    """
    Extracts the UII and the  Investment Name found on the section A of
    the downloaded PDFs.

    Parameters:
        pdf_path (str): the path of the PDF to extract the data.

    Returns:
       data (dictionary): contains the information in the format
                        {'UII':'Investment Name'}
    """
    logger.info(
        f'Extracting the data from the PDFs using regex at path: {pdf_path}')
    data = {}

    # Use regular expressions to match the UII and the Name of the Investment
    text = pdf.get_text_from_pdf(pdf_path, pages=[1])
    investment_name = string.get_regexp_matches(
        text[1], '(?<=Name of this Investment: )(.*)(?=2. Unique Investment Identifier)')
    uii = string.get_regexp_matches(
        text[1], '(?<=Unique Investment Identifier \(UII\): )(.*)(?=Section B)')

    # Stores the UII and the Investment Name in a dictionary and return it
    data['uii'] = uii[0]
    data['investment_name'] = investment_name[0]

    return data


def compare_pdf_with_excel(filename, data):
    """
    Takes the table of Individual Investments of the excel file and appends
    a new column that matches the UII of the table with the UII in the data
    extracted from the PDF.

    Returns:
        df_new_investments_table (df): same investments table with a new column
                                        that contains the Investment Name
                                        extracted from the PDF.
    """
    logger.info(
        'Comparing the data from the PDF with the Investments Table\
                in the excel file')
    df_new_investments_table = pd.read_excel(
        filename, sheet_name=config()['agency'][0:30])

    # Loop through each UII in the df and check if it exists in the data
    # dictionary then populates a list with the Investment Name that matches
    # each UII and if it is not found appends 'Not in PDF'.
    new_column = []
    for elem in df_new_investments_table['UII']:
        if elem in data:
            new_column.append(data[elem])
        else:
            new_column.append('Not in PDF')

    # Creates a new column for the table and returns the df
    df_new_investments_table['Title in PDF'] = new_column

    return df_new_investments_table


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

        logger.info('Updating excel file with the individual\
                investments table')
        _save_df_to_excel(
            df_individual_investments_table,
            'output/output.xlsx',
            agency[0:30],
            append=True
        )

        sleep(5)
        download_pdfs()
        sleep(5)

    finally:
        browser_lib.close_all_browsers()

    # Compare data in excel with PDFs
    data = {}

    # Fill data dictionary with each PDF information in the format:
    #   {'UII':'Investment Name'} looping through each PDF file on
    # the 'output' directory
    for current_file in pdf_path.iterdir():
        # Checking validation to scrape on PDFs only
        if str(current_file)[-4:] == '.pdf':
            raw = extract_data_from_pdf(current_file)

            data[raw['uii']] = raw['investment_name']

    # Comparing excel table with PDF data and creating new dataframe
    df_new_investments_table = compare_pdf_with_excel(
        './output/output.xlsx', data)

    logger.info('Saving comparison table into at sheet "PDF comparison"')
    _save_df_to_excel(
        df=df_new_investments_table,
        filename='output/output.xlsx',
        sheet_name='PDF comparison',
        append=True
    )

    pdf.close_all_pdfs()


# Call the main() function,
# checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
