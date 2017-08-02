# news_crawler

This is a web crawler that collects Daum News (http://media.daum.net/) article data, developed for the purpose of developing an engine that can distinguish fake news from real ones.

* Dependencies:
  * BeautifulSoup (bs4)
    * For more info on the library, check out: https://www.crummy.com/software/BeautifulSoup/
  
* Using the Daum News Crawler:
  * Enter the start date (the more recent date) and the end date in the format 'YEARMNDY' (e.g. 20170710)
  (e.g. if collecting from range 07/08/17 ~ 07/13/17, start date = 20170713 and end date = 20170708)
  * If you wish to edit the sections from which you wish to collect article data, edit DEFAULT_SEC_LIST
  
