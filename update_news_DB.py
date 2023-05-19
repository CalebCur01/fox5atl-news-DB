import os, sys, bs4, requests, webbrowser, re, spacy
from heapq import nlargest
from pathlib import Path
import datetime
import sqlite3


def write_pagelist():
    with open('pagelist.txt','w+') as file:
        for page in pagelist:
            file.writelines(f"{page}\n")

def load_pagelist():
    with open('pagelist.txt','r') as file:
        pagelist = [current_page.rstrip() for current_page in file.readlines()]
        return pagelist

def write_curID(value):
    with open ('current_ID.txt','w+') as file:
        file.write(str(value))
def get_curID():
    with open ('current_ID.txt','r') as file:
        return int(file.readline())



#We load our current ID and list of pages we've already visited
pagelist = []
curID = get_curID()
pagelist = load_pagelist()



#load database
filepath = 'D:/database/foxnewsDB.db'
try:
    conn = sqlite3.connect(filepath)
    print("Database succesfully opened")
except Error as e:
    print(e)
cursor = conn.cursor()

#cursor.execute("CREATE TABLE news_articles(id INTEGER PRIMARY KEY, link TEXT, insertion_date TIMESTAMP, title TEXT, author TEXT, publication_date TEXT, tag TEXT, content TEXT)")

#We start from the main news page
url = "https://www.fox5atlanta.com/news"

# We load nlp pre-trained model and get a bs4 object for the webpage
req = requests.get(url)
soup = bs4.BeautifulSoup(req.text, "html.parser")
nlp = spacy.load('en_core_web_sm')

# First we list all <article> tags
articleList =[]
newsList = []
for article in soup.find_all('article'):
    articleList.append(article)

# We then remove any videos
for article in articleList:
    page = article.find("a")['href']
    link = "https://www.fox5atlanta.com" + page
    if not "video" in link:
        newsList.append(link)

# Now we go through and get the text from each article
for news in newsList:
    print(news)

    #We skip a page if it's already been visited
    if(news in pagelist):
        print("Page already stored\n\n")
        continue

    #Now we parse the news article
    req = requests.get(news)
    soup = bs4.BeautifulSoup(req.text,"html.parser")

    #We get the Title
    title_tag = soup.find('h1',class_="headline")
    if title_tag == None:
        title = "No title found"
    else:
        title = title_tag.text.replace("\n","")
    print(title)

    #We get the author
    author_tag = soup.find('div',class_="author-byline")
    if author_tag == None:
        author = "Unknown"
    else:
        author = author_tag.text[3:].replace("\n","")
    print(author)

    #We try to get the article keyword
    meta_tag = soup.find('div',class_="article-updated")
    if meta_tag == None or "Updated" in str(meta_tag):
        keyword = "No tag found"
    else:
        keyword = meta_tag.text.replace("\n","")
    print(keyword)
    

    #We get the date published
    date_tag = soup.find('div',class_="article-date")
    if date_tag == None:
        date = "No date found"
    else:
        date = date_tag.text[10:].replace("\n","")
    print(date)

    #We assign the article text into a variable called content
    article = soup.find('div',class_="article-body")
    paragraphs = article.find_all('p')
    content = ' '.join([paragraph.get_text(strip=True) for paragraph in paragraphs])
    if content == "":
        content = "No content found"

    #We add the entry to our database
    curTime = datetime.datetime.now()
    cursor.execute("INSERT into news_articles VALUES(?,?,?,?,?,?,?,?)",(curID,news,curTime,title,author,date,keyword,content))
    print("Successfully added to database!\n\n")
    pagelist.append(news)
    curID += 1
    conn.commit()
    

# All done!
changes = conn.total_changes
conn.close()
write_curID(curID)
write_pagelist()

print(f"Successfully made {changes} changes")
exitvar = input("Done! press any key to exit...")
    



    
