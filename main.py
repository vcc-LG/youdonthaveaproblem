import requests
import json
import random
import re
import base64
import os
import tweepy

CONSUMER_KEY = "YOUR_API_KEY"
CONSUMER_SECRET = "YOUR_API_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
ACCESS_TOKEN_SECRET = "YOUR_ACCESS_TOKEN_SECRET"

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)

url = 'https://en.wikipedia.org/w/api.php?format=json&action=query&generator=random&grnnamespace=0&prop=revisions%7Cimages&rvprop=content&grnlimit=10'
vowels = ('a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U')
regex = re.compile(".*?\((.*?)\)")
filename = 'temp.jpg'


def save_profile_image(title):
    try:
        os.remove(filename)
    except Exception as e:
        pass
    profile_image_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=' + \
        title + '&prop=pageimages&format=json&pithumbsize=100'
    profile_request = requests.get(profile_image_url, stream=True).json()
    for item in profile_request['query']['pages']:
        data = profile_request['query']['pages'][item]
        if data.get('thumbnail'):
            image_file_url = data.get('thumbnail')['source']
            try:
                img_data = requests.get(image_file_url).content
                with open(filename, 'wb') as handler:
                    handler.write(img_data)
                return True
            except Exception as e:
                return False
    return False


def title_list_from_json(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(re.sub("[\(\[].*?[\)\]]", "", v)
                               ) if not 'File:' in v else 0
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def indefinite_article(string):
    return 'an' if string.startswith(vowels) else 'a'


def compose_and_post_tweet(titles):
    first_title = random.choice(titles).strip()
    second_title = random.choice(titles).strip()
    first_indefinite_article = indefinite_article(first_title)
    second_indefinite_article = indefinite_article(first_title)
    second_noun = random.choice(['opportunity', 'deficiency'])
    tweet_string = 'You don\'t have %s %s problem - You have %s %s %s!' % (
        first_indefinite_article, first_title, second_indefinite_article, second_title, second_noun)
    first_choice_title, second_choice_title = [random.choice([first_title, second_title]), random.choice([first_title, second_title])]
    if save_profile_image(first_choice_title) == True:
        api.update_with_media(filename, status=tweet_string)
        print('Posted tweet with media')
    else:
        if save_profile_image(second_choice_title) == True:
            api.update_with_media(filename, status=tweet_string)
            print('Posted tweet with media')
        else:
            api.update_status(tweet_string)
            print('Posted tweet')
    return


def raw_data():
    resp = requests.get(url=url)
    return resp.json()


def interpolate_titles_and_tweet():
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)
    titles = title_list_from_json(raw_data(), 'title')
    if titles:
        compose_and_post_tweet(titles)


if __name__ == "__main__":
    interpolate_titles_and_tweet()
