from RPA.Browser.Selenium import Selenium
from time import sleep

browser_lib = Selenium()


def open_the_website(url):
    browser_lib.open_available_browser(url)


def click_dive_in():
    button_xpath = '//*[@id="node-23"]/div/div/div/div/div/div/div/a'
    browser_lib.click_element_when_visible(button_xpath)

def get_agencies():
    agencies = browser_lib.get_webelements('//div[@class="col-sm-4 text-center noUnderline"]/div/div/div/div/a/span')
    print(agencies[0].text)



# Define a main() function that calls the other functions in order:
def main():
    try:
        open_the_website("https://itdashboard.gov/")
        click_dive_in()
        sleep(5)
        print('terminado')
        get_agencies()
    finally:
        browser_lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
