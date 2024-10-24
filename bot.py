import torch # type: ignore
from transformers import BertTokenizer, BertModel # type: ignore
import boto3 # type: ignore
from sklearn.metrics.pairwise import cosine_similarity # type: ignore
import numpy as np
import time
from bs4 import BeautifulSoup # type: ignore
from csv import DictReader
from emailer import send_email


from selenium import webdriver  # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.common.keys import Keys # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.firefox.options import Options # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore

import platform
import os
from pathlib import Path




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




tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

dynamodb = boto3.resource('dynamodb',
                          region_name='',
                          aws_access_key_id='',
                          aws_secret_access_key=''
                          )

table = dynamodb.Table('ChatbotTrainingData')
matchedListingsTable = dynamodb.Table('ListingsData')
messagesTable = dynamodb.Table('MessagesData')



def load_training_data():
    response = table.scan()
    questions_answers = {}
    for item in response['Items']:
        question = item['question']
        answer = item['answer']
        questions_answers[question] = answer
    return questions_answers

def get_embedding(text):

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].numpy()

def get_response(user_input, chat_link, questions_answers=load_training_data()):
    user_embedding = get_embedding(user_input)
    best_match = None
    best_score = -1
    best_question = ""

    for question, answer in questions_answers.items():
        question_embedding = get_embedding(question)
        similarity = cosine_similarity(user_embedding, question_embedding)[0][0]

        if similarity > best_score:
            best_score = similarity
            best_match = answer
            best_question = question

    if best_score > 0.8:
        return best_match
    
    else:
        """
        send email to user if can't find response
        get password for gmail here: https://security.google.com/settings/security/apppasswords
        
        me = dcbz hyow plry kzhn

        """
        SENDER_EMAIL = ""
        SENDER_PASSWORD = ""
        RECIPIENT_EMAIL = ""
        SUBJECT = ""
        BODY = ""
        send_email(SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL, SUBJECT, BODY)
        return 
    
def add_training_data(question, answer, questions_answers=load_training_data()):

    questions_answers[question] = answer
    table.put_item(
        Item={'question': question, 'answer': answer},
        
        )
    print("Training data added successfully.")


"""
-------------------messaging functions----------------------------------------------
"""
def get_cookies_values(file):
    with open(file, encoding='utf-8-sig') as f:
        dict_reader = DictReader(f)
        list_of_dicts = list(dict_reader)
    return list_of_dicts


def all_ongoing_texts_with_client(driver):
    all_texts = driver.find_elements(By.XPATH, '//div[@dir="auto"]')
    return [i.text for i in all_texts]


def message_clients(driver):

    while True:
        print('in the message clients function now')
        matchedListings = matchedListingsTable.scan()
        
        try:
            for item in matchedListings['Items']:
                URL = item['listing_url']


            # URL = "https://www.facebook.com/marketplace/item/2470984673292700/?ref=browse_tab&referral_code=marketplace_top_picks&referral_story_type=top_picks"

            
            
                driver.get(URL)

                cookies = get_cookies_values(cookies_file)
                for i in cookies:
                    driver.add_cookie(i)
                driver.refresh()

                soup = BeautifulSoup(driver.page_source, 'html5lib') 
                links = soup.findAll('a', attrs={'class': 'x972fbf'})
                profile_links = [i.get('href') for i in links if 'profile' in i.get('href')]
                profile_id = profile_links[0].split('/')[3]
                messenger_link = "https://www.facebook.com/messages/t/" + profile_id

                #put profile_id in the driver.get below
                #"https://www.facebook.com/messages/t/100014276325191"
                driver.get(messenger_link)

                time.sleep (10)
                texts = all_ongoing_texts_with_client(driver)
                """
                after this:
                    keep track of the last sent or received message, 
                    check if there's a change in the messages list
                    if yes, it means client messaged so you should send a message back
                    if no, client has not messaged back so no need to send a message
                """
                theElement = driver.find_element(By.XPATH, '//div[@aria-label="Message"]')

                # if it's the first contact
                if len(texts) == 0:
                    message = f"Hi there, just saw that you're selling this {URL} on marketplace. Hoping I can make an offer. Can I give you something close to ${item['price']}?"
                    for i in message:
                        theElement.send_keys(i)
                    #send the first message
                    theElement.send_keys(Keys.RETURN)
                    #save the first message to the MessagesData DB
                    driver.implicitly_wait(20)
                    messagesTable.put_item(
                        Item= {
                            'messenger_link': messenger_link,
                            'product_url': URL,
                            'recent_message': message
                        },

                    )


                    SENDER_EMAIL = ""
                    SENDER_PASSWORD = ""
                    RECIPIENT_EMAIL = ""
                    SUBJECT = ""
                    BODY = ""
                    send_email(SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL, SUBJECT, BODY)
                                
                    print("sent and saved first message")

                #if we're replying to the client
                elif len(texts) > 0:
                    recent_message = ""
                    payload = messagesTable.get_item(
                        Key={'product_url': URL},
                        ProjectionExpression='recent_message'
                    )
                    print("about to check if item not in payload")
                    if 'Item' not in payload:
                        messagesTable.put_item(
                                    Item={
                                        'messenger_link': messenger_link,
                                        'product_url': URL,
                                        'recent_message': ""
                                    },

                        )
                    
                    
                    currentChat = messagesTable.get_item(Key={'product_url': URL})


                    #get the most recent message sent
                    
                    recent_message = currentChat['Item']['recent_message']
                    #if the most recent message is not the same as the message in the messaging area, we have a response
                    if texts[-1] != recent_message:
                        #get the response from the AI bot and send it
                        message = get_response(texts[-1], messenger_link)
                        recent_message = message
                        for i in message:
                            theElement.send_keys(i)
                        theElement.send_keys(Keys.RETURN)
                        driver.implicitly_wait(20)


                        #now update the recent message of that chat
                        #if we can find the current chat item in the DB, we update the most recent message
                        if len(currentChat['Item']) == 1:
                            messagesTable.update_item(
                                Key={'product_url': URL},
                                UpdateExpression='SET recent_message = :val',
                                ExpressionAttributeValues={':val': recent_message}
                            )
                            print("updated the message in the DB")
                        #else we create a new chat in the DB 
                        else:
                            messagesTable.put_item(
                                Item={
                                    'messenger_link': messenger_link,
                                    'product_url': URL,
                                    'recent_message': recent_message
                                },

                            )
            time.sleep(5 * 60)
                
        except Exception as e:
            print("error: ", str(e))



