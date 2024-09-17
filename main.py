import json
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
from json.decoder import JSONDecodeError
import praw
from urllib.parse import urlparse
import bs4
from dotenv import load_dotenv
import os

load_dotenv()

client_id=os.getenv('client_id')
client_secret=os.getenv('client_secret')
user_agent=os.getenv('user_agent')
    
print(client_id + " here")
reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    user_agent = user_agent,
)

start = datetime.now()
current_time = start.strftime("%H:%M:%S")
print("Current Time =", current_time)

def getTitleFromHtmlPage(url):
    page = ""
    soup = ""
    try:
        page = requests.get(url, timeout=30)
    except requests.Timeout:
        print("Timeout Error")
        page = ""
    except requests.ConnectionError:
        print("Connection Error")
        page = ""
    except requests.HTTPError:
        print("Http Error")
        page = ""
    except Exception:
        print("Exception Error")
        page = ""

    try:
        if page != "":
            soup = BeautifulSoup(page.content,"html.parser")
            if soup.title:
                return soup.title.string
    except bs4.ParserRejectedMarkup:
        print("Parser Error")
    except Exception:
        print("Exception Error")
    return ""




    


def getUrlsFromRedditPosts(bodyurl, bodyselftext):
    urls=[]
    if not bodyselftext:
        urlAndTitleObj = {
            "url": [bodyurl],
            "title": getTitleFromHtmlPage(bodyurl)
        }
        urls.append(urlAndTitleObj)
    else:
        findUrls = re.findall( r'\((https?://[^\s()]+)', bodyselftext)
        findUrls = list(set(findUrls))
        
        for url in findUrls:
            findTitle = getTitleFromHtmlPage(url)
            urlAndTitleObj = {
                "url": url,
                "title": findTitle
            }
            urls.append(urlAndTitleObj)
    return urls
        
def arrayOfIds(loadFromJson):
    ids = []
    for redditObjs in loadFromJson:
        ids.append(redditObjs["id"])
    return ids



appendToJson = []
loadFromJson = []
subreddit = reddit.subreddit("tennis")
subOne = subreddit.hot(limit = None)
subTwo = subreddit.new(limit = None)
subThree = subreddit.top(limit=None)
subFour = subreddit.rising(limit = None)


try:
    with open('./extra.json', 'r') as input:
        loadFromJson = json.load(input)
except JSONDecodeError:
    print("JSON file is empty.")

submissionID = set(arrayOfIds(loadFromJson))
listOfSubredditRank = [subOne, subTwo, subThree, subFour]
# listOfSubredditRank = [subreddit.new(limit=200)]

cnt = 1
for sort in listOfSubredditRank:
    for submission in sort:
        print(cnt)
        cnt += 1
        print(submission.id)
        print(submission.url)
        if submission.id not in submissionID:
            submissionAuthor = ""
            if submission.author is not None and submission.author.name is not None:
                submissionAuthor = submission.author.name
            else:
                submissionAuthor = "[deleted]"
            submissionScore = submission.score
            submissionTitle = submission.title
            submissionId = submission.id
            submissionBody =submission.selftext
            submissionNumOfComments = submission.num_comments
            submissionUrl = submission.url
            redditObj = {
                "author": submissionAuthor,
                "score" : submissionScore,
                "title" : submissionTitle,
                "id" : submissionId,
                "body": submissionBody,
                "numberOfComments": submissionNumOfComments,
                "url": submission.url,
                "titlesForExternalWebpage": [],
                "comments": []
            }
            if not submission.selftext:
                redditObj["url"] = submission.shortlink



            redditObj["titlesForExternalWebpage"] = getUrlsFromRedditPosts(submissionUrl, submissionBody)
            submissionID.add(submissionId)
            submission.comments.replace_more(limit = 0)
            comments = submission.comments.list()

        
            for comment in comments:
                redditObj["comments"].append(comment.body)
            for i in range(min(len(comments), 100)):
                redditObj["comments"].append(comments[i].body)

            loadFromJson.append(redditObj)
    try:
        with open('./extra.json', 'w') as output:
            json.dump(loadFromJson, output, indent=4)
    except (TypeError, ValueError) as e:
        print(f"Error dumping JSON data: {e}")

    print("f")




print("Complete")
finish = datetime.now()
finish_time = finish.strftime("%H:%M:%S")
print("Finish Time =", finish_time)
