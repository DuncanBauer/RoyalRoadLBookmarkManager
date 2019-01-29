# Usage:
#  > royalroad.py [db ip] [db username] [db password] [royalroad username] [royalroad password]
#         0          1           2            3                 4                      5
#  > royalroad.py [db ip] [db username] [royalroad username] [royalroad password]
#         0          1           2                 4                      5


import sys
import re
import time
import math
import pyrebase
import requests, lxml
import getpass
import threading
import json
from bs4 import BeautifulSoup
from classes import Story
from classes import Chapter
from classes import RoyalRoadSoupParser

MAIN_MENU_SIZE = 3
firebase = None
with open('config.json') as f:
    config = json.load(f)
    firebase = pyrebase.initialize_app(config)

user = firebase.auth().sign_in_with_email_and_password(config['email'], config['password'])
startTime = time.time()
db = firebase.database()
db.child("stories").remove()

stories = []

url = 'https://www.royalroad.com/account/login'
url2 = 'https://royalroad.com'
suffix = '/my/bookmarks?page='

headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'accept-encoding': 'gzip',
           'accept-language': 'en-US,en;q=0.9',
           'cache-control': 'no-cache',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
           'Content-Type': 'application/x-www-form-urlencoded',
           'Connection': 'keep-alive'}


def rec_storypush(i, links):
    # links[i] is for the story
    # links[i+1] is for the author
    if i >= len(links) - 1:
        return []
    else:
        return [Story(links[i].text, links[i]['href'], links[i+1].text, links[i+1]['href'])] + rec_storypush(i + 2, links)

def rec_bookmarkget(i, s):
    print(threading.current_thread().getName(), 'Starting')
    # Load new page to get story titles, links, and authors
    p = s.get(url2 + suffix + str(i))
    # Create soup to parse html
    soup = BeautifulSoup(str(p.text), "lxml")

    # Search soup for all story titles, authors, and links
    links = RoyalRoadSoupParser.grab_story_titles_authors_links(soup)

    temp = rec_storypush(0, links)
    global stories
    stories = stories + temp
    print(threading.current_thread().getName(), 'Exiting')


def chapter_get(i, s):
    print(threading.current_thread().getName(), 'Starting')
    # Grab link to new story
    global stories
    story_link = stories[i].getStoryLink()
    # Load new page to get chapter titles, links, and upload times
    p = s.get(url2 + story_link)
    # Create soup to parse html
    soup = BeautifulSoup(str(p.text), 'lxml')

    times = soup.find_all("time", format='agoshort')
    links = [a for a in soup.find_all("a", href=True) if a['href'].startswith(stories[i].getStoryLink()) \
        and not a['href'].startswith(stories[i].getStoryLink() + '?reviews=')]

    for a in range(1, len(links), 1):
        # Create new chapter
        newChapter = Chapter()
        newChapter.setStoryLink(story_link)
        newChapter.setChapterLink(links[a]['href'])
        newChapter.setChapterName((links[a].get_text()).strip())
        newChapter.setChapterTime(times[a - 1].text)
        stories[i].addChapter(newChapter)
    print(threading.current_thread().getName(), 'Exiting')

def fetchall():
    retry = True
    sesh = None

    #if(not empty_db(connection)):
    #    return 0

    session = requests.Session()
    with session as s:
        retry = True
        while retry:
            username = input("Enter RoyalRoad username: ")
            password = getpass.getpass("Enter RoyalRoad password: ")
            payload = {'Username': username,
                       'Password': password}
            print("Attempting to log in to RoyalRoad...")
            print()
            p = s.post(url, data=payload, headers=headers)
            if p.url.endswith("loginsuccess"):
                retry = False
            else:
                print("Unsuccessful login. Please try again")

        print("Parsing data...")
        p = s.get(url2 + '/my/bookmarks')

        # Create soup to parse html
        soup = BeautifulSoup(str(p.text), "lxml")

        # Search soup for all links to other bookmark pages
        bookmark_number = RoyalRoadSoupParser.grab_bookmark_number(soup)
        ticks = time.time()

        threads = []
        for i in range(0, bookmark_number + 2, 1):
            threads.append(threading.Thread(target=rec_bookmarkget, args=(i, s,), daemon=False))
        [t.start() for t in threads]
        [t.join() for t in threads]

        #stories = rec_bookmarkget(1, bookmark_number + 1, s)
        print("Time reading bookmark pages: ", time.time() - ticks)
        ticks = time.time()

        threads = []
        for i in range(0, len(stories), 1):
            threads.append(threading.Thread(target=chapter_get, args=(i, s,), daemon=False))
        [t.start() for t in threads]
        [t.join() for t in threads]

        print("Time reading story chapters: ", time.time() - ticks)
        ticks = time.time()

        threads = []
        for i in range(0, len(stories), 1):
            threads.append(threading.Thread(target=rec_store_story, args=(i,), daemon=False))
        [t.start() for t in threads]
        [t.join() for t in threads]


        print("Time writing to DB: ", time.time() - ticks)
        ticks = time.time()

        return 1

def rec_store_story(i):
    print(threading.current_thread().getName(), 'Starting')
    global stories
    if i < len(stories):
        pattern = re.compile('[\W_]+')
        data = {
            'title': stories[i].getTitle(),
            'author': stories[i].getAuthor(),
            'storyLink': stories[i].getStoryLink(),
            'authorLink': stories[i].getAuthorLink(),
            'lastUpdated': str(stories[i].getLastUpdated())
        }
        titi = pattern.sub('', data['title'])
        key = db.child("stories").child(titi).set(data)

        rec_store_chap(db, i, 0, titi)
    print(threading.current_thread().getName(), 'Exiting')

def rec_store_chap(connection, i, a, titi):
    global stories
    if a < stories[i].getChapterCount():
        pattern = re.compile('[\W_]+')
        chapts = stories[i].getChapters()
        data = {
            'title': chapts[a].getChapterName(),
            'chaptLink': chapts[a].getChapterLink(),
            'storyLink': stories[i].getStoryLink(),
            'timePublished': chapts[a].getChapterTime()
        }
        tit = pattern.sub('', data['title'])
        results = db.child("stories").child(titi) \
                    .child("chapters").child(tit).set(data)
        rec_store_chap(db, i, a + 1, titi)

def fetchlatest(payload, url, url2, suffix, last_check):

    print("Entering...")

    parser = RoyalRoadSoupParser()
    session = requests.Session()
    with session as s:
        # Log in to royalroad.com and go to bookmarks page
        s.post(url, data=payload)

        p = s.get(url2 + '/my/bookmarks')
        soup = BeautifulSoup(str(p.text), "lxml")
        bookmark_numbers = parser.grab_bookmark_numbers(soup)

        p = s.get(url2 + suffix + str(bookmark_numbers[0]))
        soup = BeautifulSoup(str(p.text), "lxml")

        search_bookmarks(s, url2, suffix, bookmark_numbers, 0, last_check, parser, (0, 0))

        return math.floor(time.time())

def search_bookmarks(s, url, suffix, bookmark_numbers, curr_bookmark_number, last_check, parser, result):
    print(url + suffix + str(curr_bookmark_number + 1))
    story_offset = 1

    # Load new bookmark page
    p = s.get(url + suffix + str(curr_bookmark_number + 1))
    soup = BeautifulSoup(str(p.text), "lxml")
    story_links = parser.grab_story_links(soup)

    # Loads page of last story on bookmark page
    p = s.get(url + story_links[len(story_links) - story_offset])
    soup = BeautifulSoup(str(p.text), "lxml")

    # Checks the date of the most recently posted chapter with last time the db was updated
    result = check_story(soup, parser, last_check, (0,0))
    found = False

    print("Current_bookmark_number: " + str(curr_bookmark_number))
    print("Bookmarks: " + str(bookmark_numbers))

    while (not found) and (story_offset < len(story_links)) and (curr_bookmark_number < len(bookmark_numbers)):
        print("Result: " + str(result))
        if result == (1, 0):
            curr_bookmark_number += 1
            search_bookmarks(s, url, suffix, bookmark_numbers, curr_bookmark_number, last_check, parser, result)

        elif result == (0, 1):
            story_offset += 1
            p = s.get(url + story_links[len(story_links) - story_offset])
            soup = BeautifulSoup(str(p.text), "lxml")
            result = check_story(soup, parser, last_check, result)

        if result == (0, 0):
            found = True

        print("Story offset: " + str(story_offset))
        print("Story_links length: " + str(len(story_links)))
        print("Story_links length - offset: " + str(len(story_links) - story_offset))
        print()

    print("Current bookmark page: " + str(curr_bookmark_number + 1))
    print("Current Story number: " + str(len(story_links) - story_offset + 1))
    print()

# (1, 0) - go to next bookmark page
# (0, 1) - begin ascending current bookmark page
# (0, 0) - found the chapter updated immediately after the last db update
def check_story(soup, parser, last_check, found):
    # Search soup for all chapter upload times
    chapter_times = parser.grab_chapter_times(soup)

    # If the chapter is more recent and is ascending, return (0, 0)
    if int(chapter_times[len(chapter_times) - 1]) >= last_check and found == (0, 1):
        return (0, 0)
    # If the chapter is not more recent return (0, 1)
    elif int(chapter_times[len(chapter_times) - 1]) < last_check:
        return (0, 1)
    # If the chapter is more recent than the last update return (1, 0)
    elif int(chapter_times[len(chapter_times) - 1]) >= last_check:
        return (1, 0)

def check_last_updated():
    print("calling")

switch = {
    '1': fetchall,
    '2': fetchlatest,
    '3': check_last_updated
}


if __name__ == "__main__":
    connection = None

    print()
    print("*****************************************************************")
    print("* Welcome to the RoyalRoad Bookmark Cataloger\n*")
    print("* Commands:")
    print("* 1 - Reinitialize database")
    print("* 2 - Update database")
    print("* 3 - Check Last Updated")
    print("*****************************************************************")

    retry = True
    while retry:
        command = input("> ")
        if int(command) <= 0 or int(command) > MAIN_MENU_SIZE:
            command = input("Invalid input. Retry (y/n)? ")
        else:
            retry = False
            func = switch.get(str(command))
            print()
            func()
