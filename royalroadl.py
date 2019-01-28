# Usage:
#  > royalroad.py [db ip] [db username] [db password] [royalroad username] [royalroad password]
#         0          1           2            3                 4                      5
#  > royalroad.py [db ip] [db username] [royalroad username] [royalroad password]
#         0          1           2                 4                      5


import sys
import time
import math
import pyrebase
import requests, lxml
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from classes import Story
from classes import Chapter
from classes import RoyalRoadSoupParser
from classes import BookmarkManager

MAIN_MENU_SIZE = 3

def createStory(iterator):
    print("Pre: ", iterator)
    enumerate(iterator)
    print("Post: ", iterator)
    return iterator

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print("Encountered a start tag:", tag)

    def handle_endtag(self, tag):
        print("Encountered an end tag :", tag)

    def handle_data(self, data):
        print("Encountered some data  :", data)

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

def db_connect():
    connection = BookmarkManager()
    db_ip = input("Enter database ip: ")
    username = input("Enter database username: ")
    password = input("Enter database password: ")
    ticks = time.time()
    print()
    print("Connecting to database...")
    connection.connect(db_ip, username, password, 'royalroad', 'utf8')
    print("Connection to database established!")

    print("Time spend connecting to db: ", time.time() - ticks)
    return connection

def empty_db(connection):
    try:
        connection.query(("""DROP TABLE IF EXISTS bookmarks""", ())) # To be removed after updating script is complete
        connection.query(("""DROP TABLE IF EXISTS chapters""", ()))  # To be removed after updating script is complete

        connection.query(("""CREATE TABLE IF NOT EXISTS `bookmarks` (
                 `title` varchar(200) NOT NULL,
                 `author` varchar(199) DEFAULT NULL,
                 `link` varchar(199) NOT NULL,
                 `authorLink` varchar(199) DEFAULT NULL,
                 `lastUpdated` varchar(45) NOT NULL,
                 PRIMARY KEY (`link`),
                 UNIQUE KEY `link_UNIQUE` (`link`)
                 )ENGINE=InnoDB DEFAULT CHARSET=utf8""", ()))
        connection.query(("""CREATE TABLE IF NOT EXISTS `chapters` (
                 `fictionLink` varchar(199) NOT NULL,
                 `chapterTitle` varchar(199) NOT NULL,
                 `chapterLink` varchar(199) NOT NULL,
                 `postTime` varchar(45) NOT NULL,
                 PRIMARY KEY (`chapterLink`)
                 )ENGINE=InnoDB DEFAULT CHARSET=utf8""", ()))
        c = connection.query(("""SELECT count(*) as tot FROM bookmarks""", ()))

    except Exception as e:
        print("Exception Thrown: " + str(e))
        print("Failed to initialize database...")
        return 0
    return 1

def rec_storypush(i, links):
    # links[i] is for the story
    # links[i+1] is for the author
    if i >= len(links) - 1:
        return []
    else:
        return [Story(links[i].text, links[i]['href'], links[i+1].text, links[i+1]['href'])] + rec_storypush(i + 2, links)

def rec_bookmarkget(i, bookmark_number, s):
    stories = []
    if i <= bookmark_number:
        # Load new page to get story titles, links, and authors
        p = s.get(url2 + suffix + str(i))
        # Create soup to parse html
        soup = BeautifulSoup(str(p.text), "lxml")

        # Search soup for all story titles, authors, and links
        links = RoyalRoadSoupParser.grab_story_titles_authors_links(soup)

        stories = rec_storypush(0, links)
        return stories + rec_bookmarkget(i+1, bookmark_number, s)
    else:
        return []

def fetchall(connection):
    retry = True
    sesh = None

    if(not empty_db(connection)):
        return 0

    session = requests.Session()
    with session as s:
        retry = True
        while retry:
            username = input("Enter RoyalRoad username: ")
            password = input("Enter RoyalRoad password: ")
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

        stories = rec_bookmarkget(1, bookmark_number + 1, s)
        print("Time reading bookmark pages: ", time.time() - ticks)
        ticks = time.time()


        # Begin traversing bookmarked stories to read chapter names, links, and upload times
        for i in range(0, len(stories), 1):
            # Grab link to new story
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

        print("Time reading story chapters: ", time.time() - ticks)
        ticks = time.time()

        try:
#            rec_store_story(connection, 0, stories)
            # STORE DATA IN MYSQL DB
            j = 0
            for i in stories:
                #print(j, ": ", i.getTitle())
                connection.store_story(str(i.getTitle()),
                                       str(i.getAuthor()),
                                       str(i.getStoryLink()),
                                       str(i.getAuthorLink()),
                                       str(i.getLastUpdated()))
                chaps = i.getChapters()
                for a in range(0, i.getChapterCount(), 1):
                    chapt = chaps[a]
                    #print("    ", a, ": ", chapt.getChapterName())
                    connection.store_chapter(str(i.getStoryLink()),
                                             str(chapt.getChapterName()),
                                             str(chapt.getChapterLink()),
                                             str(chapt.getChapterTime()))

        #    s.__str__()
                j = j + 1
            cur = connection.query("""SELECT * FROM chapters WHERE fictionLink = '//fiction//568/reincarnation/-first/-monster'""")
            c = cur.fetchall()
            for q in c:
                print(q)

        except Exception as e:
            print(e)
            exit()

        print("Time writing to DB: ", time.time() - ticks)
        ticks = time.time()

        return 1

def rec_store_story(connection, i, stories):
    try:
        if i < len(stories):
            print(i, ": ", stories[i].getTitle())
            connection.store_story(stories[i].getTitle(),
                                   stories[i].getAuthor(),
                                   stories[i].getStoryLink(),
                                   stories[i].getAuthorLink(),
                                   str(stories[i].getLastUpdated()))
            chaps = stories[i].getChapters()

            rec_store_chap(connection, i, 0, chaps, stories)
            rec_store_story(connection, i + 1, stories)
    except (exc):
        print(exc)

def rec_store_chap(connection, i, a, chaps, stories):
    #if not connection.is_connected():
    #    connection.reconnect()
    try:
        if a < len(chaps):
            chapt = chaps[a]
            print("    ", a, ": ", chapt.getChapterName())
            connection.store_chapter(stories[i].getStoryLink(),
                                     chapt.getChapterName(),
                                     chapt.getChapterLink(),
                                     str(chapt.getChapterTime()))
            rec_store_chap(connection, i, a + 1, chaps, stories)
    except (exc):
        print(exc)

def fetchlatest(connection, payload, url, url2, suffix, last_check):

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


def check_last_updated(connection):
    print("calling")
    print(connection.get_last_updated())


switch = {
    '1': fetchall,
    '2': fetchlatest,
    '3': check_last_updated
}


if __name__ == "__main__":
    retry = True
    connection = None
    while True:
        try:
            connection = db_connect()
            break
        except Exception as e:
            command = input("Failed to establish database connection. Retry (y/n)? ")
            if command is 'y':
                continue
            else:
                exit()

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
            func(connection)

    #is_empty = c.fetchone()
    #other = connection.query(("""SELECT lastUpdated FROM bookmarks""", ()))
    #thisone = other.fetchall()
    #for a in thisone:
    #    print(a)

    #last_check = connection.get_last_updated()
    #print(last_check)
    #last_check = grabData.fetchlatest(connection, payload, url, url2, suffix, last_check)

    connection.close()
