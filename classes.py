from MySQLConnectionManager import DB


class Chapter:

    def __init__(self):
        self.story_link   = None
        self.chapter_name = None
        self.chapter_link = None
        self.chapter_time = None

#    def __init__(self, story_link, chapter_name, chapter_link, chapter_time):
#        self.story_link   = story_link
#        self.chapter_name = chapter_name
#        self.chapter_link = chapter_link
#        self.chapter_time = chapter_time

    def setStoryLink(self, story_link):
        self.story_link = story_link

    def setChapterName(self, chapter_name):
        self.chapter_name = chapter_name

    def setChapterLink(self, chapter_link):
        self.chapter_link = chapter_link

    def setChapterTime(self, chapter_time):
        self.chapter_time = chapter_time

    def getStoryLink(self):
        return self.story_link

    def getChapterName(self):
        return self.chapter_name

    def getChapterLink(self):
        return self.chapter_link

    def getChapterTime(self):
        return self.chapter_time

    def print(self):
        print("  " + self.chapter_name)
        print("  " + self.chapter_link)
        print("  " + str(self.chapter_time))


class Story:

#    def __init__(self):
#        self.chapter_count = 0
#        self.title = None
#        self.author = None
#        self.author_link = None
#        self.story_link = None
#        self.chapters = []
#        self.last_updated = None

    def __init__(self, title, story_link, author, author_link):
        self.title = title
        self.author = author
        self.author_link = author_link
        self.story_link = story_link
        self.chapters = []
        self.chapter_count = 0
        self.last_updated = None

    def setTitle(self, title):
        self.title = title

    def setAuthor(self, author):
        self.author = author

    def setAuthorLink(self, link):
        self.author_link = link

    def setStoryLink(self, story_link):
        self.story_link = story_link

    def setChapterCount(self, chapter_count):
        self.chapter_count = chapter_count

    def setLastUpdated(self, last_updated):
        self.last_updated = last_updated

    def getTitle(self):
        return self.title

    def getAuthor(self):
        return self.author

    def getAuthorLink(self):
        return self.author_link

    def getStoryLink(self):
        return self.story_link

    def getChapterCount(self):
        return self.chapter_count

    def getChapters(self):
        return self.chapters

    def getLastUpdated(self):
        return self.last_updated

    def addChapter(self, chapt):
        self.chapters.append(chapt)
        self.setLastUpdated(chapt.getChapterTime())
        self.setChapterCount(self.getChapterCount() + 1)

    def searchByChapterName(self, name):
        for i in self.chapters:
            if(i.getChapterName() == name):
                return i
        return -1

    def searchByChapterNumber(self, index):
        if self.chapters[index] != 0:
            return self.chapters[index]
        return -1

    def print(self):
        print("Title: " + str(self.getTitle()))
        print("Author: " + str(self.getAuthor()))
        print("Link: " + str(self.getStoryLink()))
        print("Author Link: " + str(self.getAuthorLink()))
        print("Last Updated: " + str(self.getLastUpdated()))
        print("Chapters:")
        for a in self.chapters:
            a.print()
        print()


class BookmarkManager(DB):

    def __init__(self):
        super().__init__()
        self.story_count = 0
        self.chapter_count = 0

    def increment_story_count(self):
        self.story_count += 1

    def increment_chapter_count(self):
        self.chapter_count += 1

    def store_story(self, title, author, link, author_link, last_updated):
        cursor = self.query(("""INSERT INTO bookmarks(title, author, link, authorLink, lastUpdated) VALUES (%s, %s, %s, %s, %s)""",
                         (title.encode('utf8'),
                          author.encode('utf8'),
                          link.encode('utf8'),
                          author_link.encode('utf8'),
                          last_updated.encode('utf8'))))
        self.increment_story_count()
        return cursor

    def store_chapter(self, story_link, chapter_name, chapter_link, chapter_time):
        cursor = self.query(("""INSERT INTO chapters(fictionLink, chapterTitle, chapterLink, postTime) VALUES (%s, %s, %s, %s)""",
                         (story_link.encode('utf8'),
                          chapter_name.encode('utf8'),
                          chapter_link.encode('utf8'),
                          chapter_time.encode('utf8'))))
        self.increment_chapter_count()
        return cursor

# Ive run into an existential dilema
# Do i go for the less accurate string to int conversion
# Or do i load every single chapter to get its post times, id really rather not
    def get_last_updated(self):
        cursor = self.query(("""SELECT lastUpdated FROM bookmarks""", ()))

        temp = cursor.fetchall()
        newest = 0
        dates = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 3600*24,
            "week": 3600*24*7,
            "month": 3600*24*30, # Just using 30 for num of days in month, will change if needed
            "year": 3600*24*365,
        }
        for i in temp:
            if i[0] == 'None':
                continue
            else:

                tup = i[0].split(' ')
                if(tup[1].endswith('s')):
                    tup[1] = tup[1][:-1]
                print("TUP: ", tup)
                print(tup[1])
                print(dates[tup[1]])
                tup[2] = tup[0]*dates[tup[1]]


                #if int(i[0]) > highest:
                #highest = int(i[0])

        return highest


class RoyalRoadSoupParser:

    def grab_bookmark_number(soup):
        # Search soup for all links to other bookmark pages
        bookmark_links = [a["href"] for a in soup("a", href=lambda x: x and x.startswith("/my/bookmarks?page="))]
        # Return number of highest page
        return int(bookmark_links[len(bookmark_links)-1].strip("/my/bookmarks?page="))

    def grab_story_titles_authors_links(soup):
        return soup.find_all("a", class_="font-red-sunglo bold")

    def grab_chapter_times(soup):
        chapter_times = []

        # Search soup for all chapter upload times
        for a in (soup.find_all("time", unixtime=True, format='ago')):
            chapter_times.append(a['unixtime'])

        return chapter_times

    def grab_chapter_links(soup):
        chapter_links = []
        to_skip = 0

        # Search soup for links to chapters
        for a in soup.find_all("a", href=True):
            if a['href'].startswith("/fiction/chapter/"):
                if to_skip == 0:
                    to_skip = 1
                elif to_skip == 1:
                    chapter_links.append(a['href'])

        return chapter_links
