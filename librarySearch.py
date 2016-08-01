import sys
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from bs4 import BeautifulSoup
import configparser
import re
import urllib

class Book:
    def __init__(self, title):
        self.title = title
        self.ebookList = []
        self.audiobookList = []
        self.paperbookList = []

    def addFormat(self, format):
        self.format = format

    def addEbook(self, library):
        self.ebookList.append(library)

    def addAudiobook(self, library):
        self.audiobookList.append(library)

    def addPaperbook(self, library):
        self.paperbookList.append(library)

class Library:
    def __init__(self, name, url, type):
        self.name = name
        self.url = url
        self.type = type

###class BookFormat:
###    def __init__(self, type, library ):
###        self.type = type
###        self.library = library

# Open the Url
def openUrl(url):
    try:
        html = urlopen(url)
        return html
    except HTTPError as e:
        print("ERROR opening url " , url, " : ", e)
        sys.exit()
    except URLError as e:
        print("ERROR: The server for url ", url, " could not be found!")
        sys.exit()

# Remove anything in parens from the title, because it probably (hopefully) isn't something we want to search for
def stripParens(title):
    pos = title.find("(")
    if pos != -1:
        title = title[0:pos]
    return title.strip()

# get one page of titles from an amazon wishlist
def getPageOfTitles(url):
    html = openUrl(url)
    bsObj = BeautifulSoup(html.read(), "html.parser")
    titles = bsObj.find_all(id=re.compile("itemName*"))
    books = []
    for titleEntry in titles:
        title = titleEntry.get("title", "unavailable")
        if (title == "unavailable"):
            print("Warning: unavailable title skipped")
            continue
        cleanTitle = stripParens(title)
        book = Book(title)
        books.append(book)

    # If there is a next page, return the link, otherwise null
    nextLink = bsObj.find("li", class_="a-last")
    # no more pages
    if (nextLink is None) or ("a-disabled" in nextLink["class"]):
        return ("", books)
    else:
        nextUrl = config.get("Amazon", "BaseUrl") + nextLink.a["href"]
        return (nextUrl, books)

def cleanupTitle(title):
    m = re.search(r'\(.+\)', title)
    if (m):
        cleanTitle = title.replace(m.group(), "")
    else:
        cleanTitle = title
    return cleanTitle.strip()

def lookupBookAtLibrary(book, library, formatCode):
    bookTitle = cleanupTitle(book.title)
    url = library.url + "/search?custom_query=" + "title%3A(" + urllib.parse.quote_plus(bookTitle) +  ")+++formatcode%3A(" + formatCode + ")";
    html = openUrl(url)
    bsObj = BeautifulSoup(html.read(), "html.parser")

    # we only need to check if the first item is a book of the right format
    listItem = bsObj.find("div", {"class": "list_item_section"})
    if (listItem is not None):
        entry = listItem.div
        entry = entry.span
        entry = entry.a
        libraryTitle = entry.string

        if (bookTitle.startswith(libraryTitle)):
###            print("FOUND ", formatCode, " for ", bookTitle)
            return True
        else:
###            print("(b) DID NOT FIND ", formatCode, " for ", bookTitle)
            return False
    else:
###        print("(a) DID NOT FIND ", formatCode, " for ", bookTitle)
        return False





########### main ############

config = configparser.ConfigParser()
config.read("librarySearch.ini")

# Get Amazon Wish List information
s = config.get("Amazon", "WishListKeys")
wishListKeys = s.split(",")
baseWishListUrl = config.get("Amazon", "BaseUrl") + config.get("Amazon", "WishListUrl")

# Get Library information
libraryList = []
s = config.get("Libraries", "LibraryKeys")
libraryKeys = s.split(",")
for key in libraryKeys:
    libraryName = config.get(key, "Name")
    libraryUrl = config.get(key, "Url")
    libraryType = config.get(key, "Type")
    library = Library(libraryName, libraryUrl, libraryType)
    libraryList.append(library)

bookList = []
for wKey in wishListKeys:
    wishListUrl = baseWishListUrl.replace("==KEY==", wKey)
    while (wishListUrl):
        wishListUrl, pageOfTitles = getPageOfTitles(wishListUrl)
        bookList.extend(pageOfTitles)


for book in bookList:
    for library in libraryList:
        formatCode = "EBOOK"
        if (lookupBookAtLibrary(book, library, formatCode)):
            book.addEbook(library)
        formatCode = "AB"
        if (lookupBookAtLibrary(book, library, formatCode)):
            book.addAudiobook(library)
        formatCode = "BK"
        if (lookupBookAtLibrary(book, library, formatCode)):
            book.addPaperbook(library)


notFoundList = []
ebookList = []
audiobookList = []
paperbookList = []
for book in bookList:
    isEbook = False
    isAudiobook = False
    if (len(book.ebookList) == 0 and len(book.audiobookList) == 0 and len(book.paperbookList) == 0):
        notFoundList.append(book.title)
    else:
        if (len(book.ebookList) > 0):
            isEbook = True
            s = book.title + ": "
            for library in book.ebookList:
                s = s + " " + library.name + " |"
            s = s[:-1]
            ebookList.append(s)

        if (len(book.audiobookList) > 0):
            isAudiobook = True
            s = book.title + ": "
            for library in book.audiobookList:
                s = s + " " + library.name + " |"
            s = s[:-1]
            audiobookList.append(s)

        if (len(book.paperbookList) > 0):
            if (not(isEbook) and not(isAudiobook)):
                s = book.title + ": "
                for library in book.paperbookList:
                    s = s + " " + library.name + " |"
                s = s[:-1]
                paperbookList.append(s)


if (len(notFoundList) > 0) :
    print("Books Not at Library")
    for notFound in notFoundList:
        print(notFound)


if (len(ebookList) > 0) :
    print("Ebooks")
    for b in ebookList:
        print("\t", b)

if (len(audiobookList) > 0) :
    print("AudioBooks")
    for b in audiobookList:
        print("\t", b)

if (len(paperbookList) > 0) :
    print("Paper Books")
    for b in paperbookList:
        print("\t", b)

