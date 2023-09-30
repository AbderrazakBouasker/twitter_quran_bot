import requests
import datetime
import time
from bs4 import BeautifulSoup
import os
import json
import tweepy
chapter_url = 'https://api.quran.com/api/v4/chapters/{}'
verse_arabic_url = 'https://api.quran.com/api/v4/quran/verses/uthmani?verse_key={}'
verse_translation_url = 'https://api.quran.com/api/v4/quran/translations/{}?verse_key={}'
translation_list_url = 'https://api.quran.com/api/v4/resources/translations'
translation_list = []
translation_exception_list = [181,231,139,78]
verse = ''
post_content = ''
api_key=''
api_key_secret=''
bearer_token=r''
access_token=''
access_token_secret=''
#creating twitter api client ----------------------------------------------------------------------------------------------
client = tweepy.Client(bearer_token,api_key,api_key_secret,access_token,access_token_secret)
auth = tweepy.OAuth1UserHandler(api_key,api_key_secret,access_token,access_token_secret)
api = tweepy.API(auth)
#creating json file for status --------------------------------------------------------------------------------------------
os.chdir(os.getcwd())
if not os.path.exists('status.json'):
    with open('status.json','w') as file:
        file.write('{"chapter_number":1,"verse_key":1}')
#reading json file for status ---------------------------------------------------------------------------------------------
with open('status.json','r') as file:
    status = json.load(file)
    print(status)
    chapter_number = status['chapter_number']
    verse_key = status['verse_key']
#updating json file for status --------------------------------------------------------------------------------------------
def updateStatus(chapter_number,verse_key):
    with open('status.json','w') as file:
        json.dump({'chapter_number':chapter_number,'verse_key':verse_key},file)
#getting chapter name -----------------------------------------------------------------------------------------------------
def getChapterName(chapter_number):
    response_chapter_name = requests.get(chapter_url.format(chapter_number))
    if response_chapter_name.status_code == 200:
        return response_chapter_name.json()['chapter']['name_simple']
    else:
        print('error getting chapter name')
#getting verse from api ---------------------------------------------------------------------------------------------------
def getVerseText(chapter_number,verse_key):
    response_verse = requests.get(verse_arabic_url.format(str(chapter_number) + ':' + str(verse_key)))
    if response_verse.status_code == 200:
        return response_verse.json()['verses'][0]['text_uthmani']
    else:
        print('error getting verse')
#max verse key for chapter -------------------------------------------------------------------------------------------------
def getVerseMax(chapter_number):
    max_verse_key_url = 'https://api.quran.com/api/v4/verses/by_chapter/{}'
    response_max_verse_key = requests.get(max_verse_key_url.format(chapter_number))
    if response_max_verse_key.status_code == 200:
        return response_max_verse_key.json()['pagination']['total_records']
    else:
        print('error getting max verse key')
#getting translation list --------------------------------------------------------------------------------------------------
response_translation_list = requests.get(translation_list_url)
if response_translation_list.status_code == 200:
    language_exist = False
    for translation in response_translation_list.json()['translations']:
        for i in range(len(translation_list)):
            if translation['id'] in translation_exception_list or translation_list[i]['language_name'] == translation['language_name']:
                language_exist = True
                break
            else:
                language_exist = False
        if not language_exist :
            list_item = {'id': translation['id'], 'language_name': translation['language_name']}
            translation_list.append(list_item)
else:
    print('error getting translation list')
#getting translation ------------------------------------------------------------------------------------------------------
def remove_html_tags(input_text):
    soup = BeautifulSoup(input_text, 'html.parser')
    cleaned_text = soup.get_text()
    return cleaned_text
def getTranslation(translation_id,translation_language,chapter_number,verse_key):
    response_translation_verse = requests.get(verse_translation_url.format(translation_id,str(chapter_number) + ':' + str(verse_key)))
    if response_translation_verse.status_code == 200:
        translation_text = response_translation_verse.json()['translations'][0]['text']
        translation_text_cleaned = remove_html_tags(translation_text)
        return translation_language + ' : ' + translation_text_cleaned + '\n'
    else:
        print('error getting translated verse')
for language in translation_list:
    getTranslation(language['id'],language['language_name'],chapter_number,verse_key)
#combining and formatting quran api result --------------------------------------------------------------------------------
while True:
    if datetime.datetime.now().second == 00 or datetime.datetime.now().minute == 30:
        for chapter_number in range(1, 115):
            post_content = ''
            chapter_name = getChapterName(chapter_number)
            max_verse_key = getVerseMax(chapter_number)
            for verse_key in range(1, max_verse_key + 1):
                verse = getVerseText(chapter_number,verse_key)
                post_content = chapter_name + '\n' + verse + '\n'
                for language in translation_list:
                    post_content += getTranslation(language['id'],language['language_name'],chapter_number,verse_key)
                client.create_tweet(text=post_content)
                updateStatus(chapter_number,verse_key)
                print('tweeted')
                time.sleep(10)
