# Usage:
#  > royalroadl.py [db ip] [db username] [db password] [royalroadl username] [royalroadl password]
#         0          1           2            3                 4                      5
#  > royalroadl.py [db ip] [db username] [royalroadl username] [royalroadl password]
#         0          1           2                 4                      5


import sys
from classes import BookmarkManager
import requests, lxml
from html.parser import HTMLParser
import time
import math
from classes import Story
from classes import Chapter
from classes import RoyalRoadLSoupParser
from bs4 import BeautifulSoup

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

url = 'https://www.royalroadl.com/account/login'
url2 = 'https://royalroadl.com'
suffix = '/my/bookmarks?page='


def db_connect():
    connection = BookmarkManager()
    db_ip = input("Enter database ip: ")
    username = input("Enter database username: ")
    password = input("Enter database password: ")
    ticks = time.time()
    print()
    print("Connecting to database...")
    connection.connect(db_ip, username, password, 'royalroadl', 'utf8')
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
                 `authorLink` varchar(199) DEFAULT NULL,
                 `link` varchar(199) NOT NULL,
                 `lastUpdated` varchar(45) NOT NULL,
                 PRIMARY KEY (`link`),
                 UNIQUE KEY `link_UNIQUE` (`link`)
                 )ENGINE=InnoDB DEFAULT CHARSET=utf8""", ()))
        connection.query(("""CREATE TABLE IF NOT EXISTS `chapters` (
                 `fictionLink` varchar(199) NOT NULL,
                 `chapterTitle` varchar(199) NOT NULL,
                 `chapterLink` varchar(199) NOT NULL,
                 `postTime` varchar(20) NOT NULL,
                 PRIMARY KEY (`chapterLink`)
                 )ENGINE=InnoDB DEFAULT CHARSET=utf8""", ()))
        c = connection.query(("""SELECT count(*) as tot FROM bookmarks""", ()))

    except Exception as e:
        print("Exception Thrown: " + str(e))
        print("Failed to initialize database...")
        return 0
    return 1

def fetchall(connection):
    retry = True
    sesh = None
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
               'accept-encoding': 'gzip',
               'accept-language': 'en-US,en;q=0.9',
               'cache-control': 'no-cache',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Connection': 'keep-alive'}

    if(not empty_db(connection)):
        return 0

    session = requests.Session()
    with session as s:
        retry = True
        while retry:
            username = input("Enter RoyalRoadL username: ")
            password = input("Enter RoyalRoadL password: ")
            payload = {'username': username,
                       'password': password}
            print("Attempting to log in to RoyalRoadL...")
            print()
            p = s.post(url, data=payload, headers=headers)
            if p.url.endswith("loginsuccess"):
                retry = False
            else:
                print("Invalid login. Please try again")

        print("Parsing data...")
        p = s.get(url2 + '/my/bookmarks')

        # Create soup to parse html
        soup = BeautifulSoup(str(p.text), "lxml")

        # Search soup for all links to other bookmark pages
        bookmark_number = RoyalRoadLSoupParser.grab_bookmark_number(soup)
        ticks = time.time()

        stories = []
        # Begin traversing bookmark pages to read story titles, links, and authors
        for k in range(1, bookmark_number + 1, 1):
            # Load new page to get story titles, links, and authors
            p = s.get(url2 + suffix + str(k))\
            # Create soup to parse html
            soup = BeautifulSoup(str(p.text), "lxml")

            # Search soup for all story titles, authors, and links
            r = RoyalRoadLSoupParser.grab_story_titles_authors_links(soup)
            #stories1 = [createStory(a) for a in r]
            #print(stories1)
            #exit()
            for i in range(0, len(r) - 1, 2):
                #newStory = Story()
                #newStory.setTitle(r[i].text)
                #newStory.setStoryLink(r[i]['href'])
                #newStory.setAuthor(r[i + 1].text)
                #newStory.setAuthorLink(r[i + 1]['href'])

                # Add story to the list
                #stories.append(newStory)
                stories.append(Story(r[i], r[i]['href'], r[i+1], r[i+1]['href']))

        print("Time reading bookmark pages: ", time.time() - ticks)
        ticks = time.time()
        # Begin traversing bookmarked stories to read chapter names, links, and upload times
        for i in range(0, len(stories) - 1, 1):
            # Grab link to new story
            story_link = stories[i].getStoryLink()
            # Load new page to get chapter titles, links, and upload times
            p = s.get(url2 + story_link)
            # Create soup to parse html
            soup = BeautifulSoup(str(p.text), 'lxml')

            counter = 0
            to_skip = 0
            times = soup.find_all("time", format='agoshort')
            links = [a for a in soup.find_all("a", href=True) if a['href'].startswith(stories[i].getStoryLink()) \
                and not a['href'].startswith(stories[i].getStoryLink() + '?reviews=')]
            for a in links:
                # Skips first valid link as its duplicated
                if to_skip == 0:
                    to_skip = 1
                elif to_skip == 1:
                    # Create new chapter
                    newChapter = Chapter()
                    newChapter.setStoryLink(story_link)
                    newChapter.setChapterLink(a['href'])
                    newChapter.setChapterName((a.get_text()).strip())
                    newChapter.setChapterTime(times[counter].text)
                    stories[i].addChapter(newChapter)
                    counter += 1

        print("Time reading story chapters: ", time.time() - ticks)
        ticks = time.time()

        try:
            # STORE DATA IN MYSQL DB
            for i in stories:
                connection.store_story(i.getTitle(),
                                       i.getAuthor(),
                                       i.getStoryLink(),
                                       str(i.getLastUpdated()))
                chaps = i.getChapters()
                for a in range(0, i.getChapterCount(), 1):
                    chapt = chaps[a]
                    connection.store_chapter(i.getStoryLink(),
                                             chapt.getChapterName(),
                                             chapt.getChapterLink(),
                                             str(chapt.getChapterTime()))

            s.__str__()
        except Exception as e:
            print(e)
            exit()

        print("Time writing to DB: ", time.time() - ticks)
        ticks = time.time()

        return 1


def fetchlatest(connection, payload, url, url2, suffix, last_check):

    print("Entering...")

    parser = RoyalRoadLSoupParser()
    session = requests.Session()
    with session as s:
        # Log in to royalroadl.com and go to bookmarks page
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


def nothing(connection):
    print("Hello")


switch = {
    '1': fetchall,
    '2': fetchlatest,
    '3': nothing
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
    print("* Welcome to the RoyalRoadL Bookmark Cataloger\n*")
    print("* Commands:")
    print("* 1 - Reinitialize database")
    print("* 2 - Update database")
    print("* 3 - Nothing")
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
    other = connection.query(("""SELECT lastUpdated FROM bookmarks""", ()))
    thisone = other.fetchall()
    for a in thisone:
        print(a)

    last_check = connection.get_last_updated()
    print(last_check)
    #last_check = grabData.fetchlatest(connection, payload, url, url2, suffix, last_check)

    connection.close()
