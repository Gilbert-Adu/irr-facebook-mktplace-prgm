from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.common.keys import Keys # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.firefox.options import Options # type: ignore
import requests # type: ignore
import os
from pathlib import Path
import platform
import time
import boto3 # type: ignore
from csv import DictReader
import eel # type: ignore
import uuid
import bcrypt # type: ignore
import base64
import json
from tasks import insert_task_to_db, get_tasks_by_id
from scraper import scrape_listings
from bot import add_training_data, message_clients
import schedule # type: ignore
import threading

eel.init('web')


condition = {
        'new': 'new',
        'used_like_new': 'used_like_new',
        'used_good': 'used_good',
        'used_fair': 'used_fair'
}
productLineList = {
        'Apple_iPhone': 'contextual[productLine]=2652902138060172',
        'Google_Pixel': 'contextual[productLine]=2162757990428129',
        'LG_Stylo': 'contextual[productLine]=2651574631536650',
        'Samsung_Galaxy': 'contextual[productLine]=383414718923119'
}
brandList = {
        'ASUS': 'contextual[shopByBrand]=374351523161038',
        'Apple': 'contextual[shopByBrand]=645664702524673',
        'Google': 'contextual[shopByBrand]=470248020387148',
        'Huawei': 'contextual[shopByBrand]=312039862824489',
        'LG': 'contextual[shopByBrand]=405707263545930',
        'Motorola': 'contextual[shopByBrand]=2242556106072268',
        'OPPO': 'contextual[shopByBrand]=1738412922954137',
        'Samsung': 'contextual[shopByBrand]=539650716561002',
        'Vivo': 'contextual[shopByBrand]=386275831981800',
        'Xiaomi': 'contextual[shopByBrand]=1243581142486947'
}
networkList = {
        'AT&T': 'contextual[shopByFeature]=334556960594689',
        'Boost_Mobile': 'contextual[shopByFeature]=442492486555204',
        'Cricket_Mobile': 'contextual[shopByFeature]=601772740339855',
        'Metro': 'contextual[shopByFeature]=823580274675996',
        'Sprint': 'contextual[shopByFeature]=600227570446764',
        'Straight_Talk': 'contextual[shopByFeature]=1061183387416708',
        'T-Mobile': 'contextual[shopByFeature]=329920024378794',
        'Cellular': 'contextual[shopByFeature]=796035580772702',
        'Unlocked': 'contextual[shopByFeature]=388070768710864',
        'Verizon': 'contextual[shopByFeature]=649922545459723'
    }

def get_desktop_path():
    home = str(Path.home())

    if platform.system() == "Windows":
        desktop = os.path.join(home, "Desktop")
    elif platform.system() == "Darwin":
        desktop = os.path.join(home, "Desktop")
    else:
        desktop = os.path.join(home, "Desktop")
    return desktop


#create 2 files. 1). qkr.csv 2). status.json
#LOGIN_STATUS_FILE = "login_status.json"
LOGIN_STATUS_FILE = os.path.join(get_desktop_path(), "status.json")





dynamodb = boto3.resource('dynamodb',
                          region_name='',
                          aws_access_key_id='',
                          aws_secret_access_key=''
                          )

tasksTable = dynamodb.Table('TasksTable')
listingTable = dynamodb.Table('ListingsData')
messagesTable = dynamodb.Table('MessagesData')





cookies_file = os.path.join(get_desktop_path(), "qkr.csv")


@eel.expose
def delete_task_by_id(id):
    try:
        #delete item task in tasks table
        the_task = tasksTable.get_item(
            Key={
                'TaskId': id
                
            }
        )
        response = tasksTable.delete_item(
            Key={
                'TaskId': id
                
            }
        )
        print(id, " deleted from tasks table")

        #delete associated listings
        taskUrl = the_task['Item']['url']
        listingPayload = listingTable.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('task_url').eq(taskUrl)
        )
        listings = listingPayload['Items']
        LISTING_URLS = [i['listing_url'] for i in listings]



        if listings:
            for item_link in LISTING_URLS:
                #FIND PARTITION KEY
                #THEN DELETE ITEM
                listingTable.delete_item(
                        Key={
                            'listing_url': item_link
                        }
                )
            print(id, " deleted from listings table")



            #delete associated messages
            
            messagePayload = messagesTable.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('product_url').eq(LISTING_URLS[0]['listing_url'])
                )
            messages = messagePayload['Items']
            print("first_message: ", messages[0])
            if messages:
                
                for i in range(len(messages)):
                    messagesTable.delete_item(
                                Key={
                                    'product_url': messages[i]['product_url']
                                }
                    )
            print(id, " deleted from messages")


            print(id, " deleted from everywhere")
    except Exception as e:
        print("Error deleting item: ",str(e) )
    

    


def is_file_corrupt():
    try:
        with open(LOGIN_STATUS_FILE, 'r') as f:
            json.load(f)
            return False
    except (json.JSONDecodeError, FileNotFoundError):
        return True


def initialize_login_status_file():
    if not os.path.exists(LOGIN_STATUS_FILE) or is_file_corrupt():
        with open(LOGIN_STATUS_FILE, 'w') as f:
            json.dump({'is_logged_in': False}, f)

def set_login_status(is_logged_in, userId=""):
    data = {
        "is_logged_in": is_logged_in,
        "userId": userId
    }
    with open(LOGIN_STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def get_login_status():
    initialize_login_status_file()
    with open(LOGIN_STATUS_FILE, 'r') as f:
        data = json.load(f)
        return data.get('is_logged_in', False)

    
def get_user_id():
    try:
        with open(LOGIN_STATUS_FILE, 'r') as json_file:
            data = json.load(json_file)
            return data.get('userId', None)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

@eel.expose 
def teach_bot(question, answer):
    add_training_data(question, answer)
    
@eel.expose
def get_user_info():
    try:
        user_id = get_user_id()
        

        response = usersTable.scan(
        FilterExpression="UserId = :user_id",
        ExpressionAttributeValues={':user_id':user_id}
    )

        
        # Retrieve items from the response
        user = response.get('Items', [])
        tasks = get_tasks_by_id(user_id)
        return {"user": user[0], "tasks": tasks} # Return the list of items
    except Exception as e:
        print(f"An error occurred: {e}")
        return None





firefox_options = Options()
firefox_options.add_argument("--headless")

"""
util function: returns first facebook marketplace result
"""

def processCity(city):
    driver = webdriver.Firefox(options=firefox_options)
    driver.get("https://www.google.com")
    search_box = driver.find_element('name', 'q')
    search_box.send_keys("facebook marketplace "+ city)
    search_box.send_keys(Keys.RETURN)

    time.sleep(3)
    first_result = driver.find_element(By.CSS_SELECTOR, '[jsname="UWckNb"]').get_attribute('href')
    return first_result




"""
util function: creates url to be used in mktplace search
"""
def create_url(city, query, condition=[], minPrice="", maxPrice="", brand="", productLine="", network=""):
    processed_url = processCity(city) + f"search?query={query}"
    url = processed_url

    if len(condition) != 0:
        temp = "&itemCondition="
        for index in range(len(condition)):
            if index == len(condition) - 1:
                temp += condition[index]
            else:
                temp += condition[index] + '%2C'
            
        url += temp

    if len(minPrice) != 0:
        url += f"&minPrice={minPrice}"

    if len(maxPrice) != 0:
        url += f"&maxPrice={maxPrice}"

    if len(brand) != 0:
        url += f"&{brandList[brand]}"

    if len(productLine) != 0:
        url += f"&{productLineList[productLine]}"

    if len(network) != 0:
        url += f"&{networkList[network]}"

    url += "&exact=false"
    return url

@eel.expose
def expose_url(city, query, condition=[], minPrice="", maxPrice="", brandInput="", product="", networkInput=""):

        url = create_url(city=city, query=query, condition=condition, minPrice=minPrice, maxPrice=maxPrice, brand=brandInput, productLine=product, network=networkInput)
        return url


@eel.expose
def expose_create_task(user_id, url, query, city, minPrice, maxPrice, brandInput, product, networkInput, condition):
        insert_task_to_db(user_id, url, query, city, minPrice, maxPrice, brandInput, product, networkInput, condition)




"""
app function: logs into fb 
"""
@eel.expose
def login_to_facebook(city, query, condition, minPrice, maxPrice, brandInput, product, networkInput):
    

    
    url = create_url(city, query, condition=condition, minPrice=minPrice, maxPrice=maxPrice, brand=brandInput, productLine=product, network=networkInput)
    user_id = get_user_id()
    """
        insert_task_to_db(user_id, url, query, city, minPrice, maxPrice, brandInput, product, networkInput, condition)

    """
    driver.get(url)
    
    
    """
    util function: processes cookies
    """
    def get_cookies_values(file):
        if os.path.exists(file):
            with open(file, encoding='utf-8-sig') as f:
                dict_reader = DictReader(f)
                list_of_dicts = list(dict_reader)
                return list_of_dicts
        else:
            print("file path incorrect")
            return None


    try:
        cookies = get_cookies_values(cookies_file)
        for i in cookies:
            driver.add_cookie(i)
        driver.refresh()
        """
        check titles, desc, and prices of listings to see if they match what we're looking for

        def find_matches()
        1. get the created url
        2. if listed price is within range, click on each listing to check title and description to see if it matches
        3. if there's a match, send initial message and add url of the listing to db or list
        4. go check messages occassionally and respond
        """
        print("I am in facebook now")


    except Exception as e:
        # Close the browser window
        print(f"An error occurred: {e}")
    print("matches: ", scrape_listings(driver, query, int(minPrice), int(maxPrice), url))


"""
DYNAMO TABLES BELOW
"""

usersTable = dynamodb.Table('UsersTable')

"""
util function: generates a unique user id for a registered user
"""
def generate_user_id():
    user_id = str(uuid.uuid4())
    return user_id


"""
util function: checks if user already exists
"""
def user_already_exists(email):
    response = usersTable.scan(
        FilterExpression="Email = :email",
        ExpressionAttributeValues={':email':email}
    )

    items = response.get('Items', [])

    if items:
        return True
    else:
        return False

"""
util function: hash a plain text password
"""

def hash_password(plain_text_password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plain_text_password.encode('utf-8'), salt)
    return base64.b64encode(hashed_password).decode('utf-8')


"""
util function: get user by email
""" 

def get_by_email(email):
    response = usersTable.scan(
        FilterExpression="Email = :email",
        ExpressionAttributeValues={':email':email}
    )

    items = response.get('Items', [])

    if items:
        return items[0]
    else:
        print(f"No user found with email {email}")
        return None


"""
app function: registers a user
"""
@eel.expose
def irr_user_sign_up(firstName, lastName, email, password):

    #check if user already exists
    if user_already_exists(email):
        return "USER EXISTS"
    
    #if no such user exists, create account
    try:
        user_id = generate_user_id()
        hashedPassword = hash_password(password)
        usersTable.put_item(
        Item={
            'UserId': user_id,
            'firstName': firstName,
            'lastName': lastName,
            'Email': email,
            'Password': hashedPassword
        }
        )
        user = get_by_email(email)
        set_login_status(True, userId=user_id)

        payload = {"message": "success", "data": user}
        return payload
        
    #return exception if can't create user
    except Exception as e:
        print(f"An error occurred: {e}")
        return e

    
def verify_password(plain_password, hashed_password):
    """Verifies the plain password against the hashed password."""
    # Decode the base64 hashed password back to bytes
    decoded_hashed_password = base64.b64decode(hashed_password)
    return bcrypt.checkpw(plain_password.encode('utf-8'), decoded_hashed_password)

"""
app function: signs a user into their account
"""
@eel.expose
def irr_user_sign_in(email, password):

    if not user_already_exists(email):
        return "NO SUCH USER EXISTS"
    
    try:
        user = get_by_email(email)
        hashed_password = user['Password']
        if verify_password(password, hashed_password):
            set_login_status(True, userId=user["UserId"])
            tasks = get_tasks_by_id(user["UserId"])
            return {"message": "SUCCESS", "tasks": tasks}

        else:
            return {"message": "FAILED", "user": ""}


    except Exception as e:
        print(f"An error occurred: {e}")
        return e
    
initialize_login_status_file() 

"""
runs background functions when app is booted

def run_in_background():
    schedule.every(5).minutes.do(message_clients(driver))
    while True:
        schedule.run_pending()
        print("running in background")
        time.sleep(5)

"""



@eel.expose
def open_window():
    if get_login_status():
        eel.start("index.html", size=(1920, 1080))
    else:
        eel.start("splash.html", size=(1920, 1080))

def start_background_function(driver):
    threading.Thread(target=message_clients, args=(driver,), daemon=True).start()

    
if __name__ == "__main__":
    driver = webdriver.Firefox(options=firefox_options)
    start_background_function(driver)
    open_window()

    while True:
        eel.sleep(1)    

    


    

    



