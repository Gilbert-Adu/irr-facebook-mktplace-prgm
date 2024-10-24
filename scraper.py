from bs4 import BeautifulSoup # type: ignore
import time
from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.common.keys import Keys # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.firefox.options import Options # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
import asyncio
import boto3 # type: ignore
import platform
import os
from pathlib import Path
from csv import DictReader



dynamodb = boto3.resource('dynamodb',
                          region_name='',
                          aws_access_key_id='',
                          aws_secret_access_key=''
                          )

table = dynamodb.Table('ListingsData')

def get_desktop_path():
    home = str(Path.home())

    if platform.system() == "Windows":
        desktop = os.path.join(home, "Desktop")
    elif platform.system() == "Darwin":
        desktop = os.path.join(home, "Desktop")
    else:
        desktop = os.path.join(home, "Desktop")
    return desktop

cookies_file = os.path.join(get_desktop_path(), "qkr.csv")


firefox_options = Options()
firefox_options.add_argument("--headless")


def match_criteria(title, query):

    if query.lower() in title.lower():
        return True
    return False
    

def scrape_listings(driver, query, minPrice, maxPrice, taskUrl):
    
    async def scraper_helper(driver, query):

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        matches = []


        listings = soup.find_all('div', class_='x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24')
        new_driver = webdriver.Firefox(options=firefox_options)
        driver = new_driver

        for i in range(len(listings)):
            title = listings[i].find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6')
            title = title.get_text()
            if title is not None:
                    
                print(f"Match found: {title}")

                    

                link_element = listings[i].find('a', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1sur9pj xkrqix3 x1s688f x1lku1pv')
                href_value = link_element.get('href')
                price = listings[i].find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1lkfr7t x1lbecb7 x1s688f xzsf02u').get_text()
                listing_url = "https://www.facebook.com/" + href_value
                if ',' in price:
                    price = int(price[1:].replace(",", ""))
                elif ',' not in price:
                    price = int(price[1:])
                if match_criteria(title, query) and minPrice <= price <= maxPrice:
                    # and minPrice <= int(price) <= maxPrice

                    
                    driver.get(listing_url)
                    driver.implicitly_wait(10)  # Waits for 10 seconds for the page to load

                    def get_cookies_values(file):
                        with open(file, encoding='utf-8-sig') as f:
                            dict_reader = DictReader(f)
                            list_of_dicts = list(dict_reader)
                            return list_of_dicts


                    try:
                        cookies = get_cookies_values(cookies_file)
                        for i in cookies:
                            driver.add_cookie(i)
                        driver.refresh()
                    except Exception as e:
                            # Close the browser window
                            print(f"An error occurred: {e}")


                    desc_page = driver.page_source
                    desc_page_soup = BeautifulSoup(desc_page, 'html.parser')
                    descriptions = desc_page_soup.find_all('span', class_="x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u")
                    desc_text = descriptions[1].get_text()
                    # wanted some checks done on the text in the description

                    
                    """
                        put matches into database
                    """
                    match = {
                            "title": title,
                            "description": desc_text,
                            "price": price,
                            "listing_url": listing_url,
                        }
                        #put match data in table
                    table.put_item(Item={'title': title, 'description': desc_text, 'price': price, 'listing_url': listing_url,'task_url':taskUrl})
                    print("matched listing inserted into database")
                    
        driver.quit()
        return


    asyncio.run(scraper_helper(driver, query))





                    

                


        


