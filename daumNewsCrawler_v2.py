# -*- coding: utf-8 -*-
"""
Daum News Crawler

@author: 정택영(Daniel Jeong)
"""

from bs4 import BeautifulSoup
import urllib
import datetime
import json

DEFAULT_SOID = 'N' # Default start of article ID
DEFAULT_ID_LENGTH = 10
DEFAULT_URL = 'http://media.daum.net/breakingnews/{}'
PAGE_NAVI = '?page={}'
DATE_NAVI = '&regDate={}'
DEFAULT_HOST = 'http://media.daum.net/'
DEFAULT_SEC_LIST = ['politics', 'economic', 'society', 'culture', 'digital']
DATE = None # Variable to hold current date
currSecURL = None
pageNum = 1
outFile = None # File to hold articles
data = {}
startDate = ''
endDate = ''
articleNum = 0

# Class that represents a date
class Date(object):
    
    # Constructor
    def __init__(self, dateString):
        self.dateString = dateString # 'YEARMNDY'
        self.year = int(dateString[:4])
        self.month = int(dateString[4:6])
        self.day = int(dateString[6:8])

    # String representation
    def __str__(self):
        return self.dateString
    
    # Magic methods for convenient comparison
    def __gt__(self, other):
        if self.year > other.year:
            return True
        elif self.year == other.year and self.month > other.month:
            return True
        elif self.year == other.year and self.month == other.month \
            and self.day > other.day:
            return True
        else:
            return False
        
    def __lt__(self, other):
        if self.year < other.year:
            return True
        elif self.year == other.year and self.month < other.month:
            return True
        elif self.year == other.year and self.month == other.month \
            and self.day < other.day:
            return True
        else:
            return False
        
    def __eq__(self, other):
        if self.year == other.year and self.month == other.month \
            and self.day == other.day:
            return True
        else:
            return False
        
    def __ge__(self, other):
        if self > other or self == other:
            return True
        else:
            return False
    
    def __le__(self, other):
        if self < other or self == other:
            return True
        else:
            return False
        
    def prevDate(self):
        oddMonth = [1, 3, 5, 7, 8, 10, 12] # Months with 31 days
        evenMonth = [4, 6, 9, 11] # Months with 30 days
        leapYear = self.checkLeap()
        
        prevYear = self.year
        prevMonth = self.month
        prevDay = self.day
        
        if prevDay < 1:
            if prevMonth == 1:
                prevMonth = 12
                prevYear -= 1
                prevDay = 31
            else:
                prevMonth -= 1
                if prevMonth in oddMonth:
                    prevDay = 31
                elif prevMonth in evenMonth:
                    prevDay= 30
                elif prevMonth == 2:
                    if leapYear:
                        prevDay = 29
                    else:
                        prevDay = 28
        else:
            prevDay -= 1
        
        if prevMonth < 10:
            prevMonth = '0' + str(prevMonth)
        if prevDay < 10:
            prevDay = '0' + str(prevDay)
        
        dateString = str(prevYear) + str(prevMonth) + str(prevDay)
        return Date(dateString)

    def checkLeap(self):
        isLeap = None
        if self.year % 4 == 0:
            if self.year % 400 == 0:
                isLeap = True
            elif self.year % 100 == 0:
                isLeap = False
            else:
                isLeap = True
        return isLeap

def articleListCrawler(alUrl):
    print(alUrl)
    try:
        articleListReq = urllib.request.urlopen(alUrl)
    except urllib.error.HTTPError:
        print('HTTPError')
        return
        
    # Create BeautifulSoup object to read HTML data
    articleListSoup = BeautifulSoup(articleListReq, 'lxml')
    
    try:
        articleUL = articleListSoup.find('div', {'class': 'box_etc'})
        articleList = \
            articleUL.findAll('a', {'href': True, 'class': 'link_txt'})
    except AttributeError:
        outFile.close()
        return
    
    # Order crawling on all articles in list
    for article in articleList:
        # Article URL formatting
        articleUrl = article['href']
        if articleUrl == '#':
            continue
        elif articleUrl[0] == '/':
            articleUrl = alUrl + articleUrl
        
        articleCrawler(articleUrl)

def articleCrawler(aUrl):
    print(aUrl)
    try:
        articleReq = urllib.request.urlopen(aUrl)
    except urllib.error.HTTPError:
        return
    
    articleSoup = BeautifulSoup(articleReq, 'lxml')
    articleDict = {} # Dictionary containing article information
    # me2:category2 빼고 <h2 id="kakaoBody" class="screen_out">경제</h2>
    # 우선 og:article:author는 빼고 작업!
    metaFilterList = ['og:title', 'og:type', 'og:url', 'og:image',\
                      'article:published_time']
    metaList = articleSoup.findAll('meta')
    
    # Meta data parsing (메타 데이터)
    for meta in metaList:
        for metaFilter in metaFilterList:
            if metaFilter in str(meta):
                articleDict[metaFilter] = meta['content'].replace('\'','')
    try:    
        if checkRedundancy(articleDict['og:title']):
            return # If article already exists
    except KeyError:
        pass
    
    try:
        category = \
            articleSoup.find('h2', {'id': 'kakaoBody', 'class': 'screen_out'})\
                .get_text()
        articleDict['category'] = category
    except AttributeError:
        articleDict['category'] = 'Different Format'
    
    # Add list of content image URLs to article dictionary (본문 사진 URL)
    content_images = [] # List to store URLs
    articleBody = articleSoup.find('div', {'class': 'article_view'})
    
    try:
        articleImageTags = articleBody.findAll('img')
        for imgTag in articleImageTags:
            content_images.append(imgTag['src'])
    except AttributeError:
        articleDict['content_images'] = []
    articleDict['content_images'] = content_images
    
    # Add article body to article dictionary (본문)
    try:
        articleText = ''
        pTags = articleBody.findAll('p', {'dmcf-ptype': 'general'})
        for p in pTags:
            articleText += p.get_text().replace('\'','').strip() + '\n\n'
    except AttributeError:
        articleDict['content'] = ''

    finally:
        outFile.write(articleText)
        articleDict['content'] = articleText
                
    # Generate article ID (기사 ID)
    articleID = DEFAULT_SOID
    global articleNum
    articleNum += 1 # Indicates number of articles stored
    for i in range(0, DEFAULT_ID_LENGTH - len(str(articleNum))): # Formatting
        articleID = articleID + '0'
    articleID = articleID + str(articleNum)
    
    data[articleID] = articleDict
    print(articleDict) # For testing purposes        
    
def getArticleListDate(url):
    dateIndex = url.find('regDate') + 8
    date = url[dateIndex:dateIndex+8]
    return Date(date)

def getArticleDate(url):
    dateIndex = url.find('v/') + 2
    date = url[dateIndex:dateIndex+8]
    return Date(date)    
    
def checkRedundancy(title):
    exists = False
    for article in data.values():
        if article['og:title'] == title:
            exists = True
    return exists

def checkFinalPage(url):
    req = urllib.request.urlopen(url)
    soup = BeautifulSoup(req, 'lxml')
    noneFlag = soup.find('p', {'class': 'txt_none'})
    return noneFlag

if __name__ == '__main__':
    print('Daum News Crawler')
    DATE = Date(datetime.datetime.now().__str__()[:10].replace('-', ''))
    print('Please enter date in following format: YEARMNDY (YEAR/MN/DY)')
    print('(뉴스기사가 최신순으로 정리되어 있기 때문)')
    print('NOTE: \'Start Date\' = the more recent date')
    print('e.g. if 2017-06-29 ~ 2017-07-03, Start Date = 20170703 and ' + \
          'End Date = 20170629')
    
    # Get and check input
    isValid = False
    while not isValid:
        startDate = Date(input('Start Date: '))
        endDate = Date(input('End Date: '))
        # Check date validity
        if startDate >= endDate and startDate <= DATE:
            isValid = True
        if not isValid:
            print('Please enter a valid start and end date')
            
    print('Working...')
    outFile = open('Article List.txt', 'w', encoding='UTF-8')
    
    # Article crawling (기사 크롤링)
    for section in DEFAULT_SEC_LIST:
        isDone = False
        currDate = startDate
        while not isDone: # Do until crawling for each section is done
            pageNum = 1
            isFinal = False
            if currDate < endDate:
                isDone = True
                continue
            while not isFinal:
                listURL = DEFAULT_URL.format(section) + \
                    PAGE_NAVI.format(pageNum) + DATE_NAVI.format(currDate)
                articleListCrawler(listURL)
                pageNum += 1
                if checkFinalPage(listURL): 
                    isFinal = True
            if isFinal:
                currDate = currDate.prevDate()
        print('SECTION(' + section + ') DONE')
    
    outFile.close()
    
    # Save data in JSON file format
    with open('data.json', 'w') as fp:
        json.dump(data, fp)
        
    print('Success')