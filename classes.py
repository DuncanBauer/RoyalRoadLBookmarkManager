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
