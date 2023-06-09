import os, sys, bs4, requests, webbrowser, re
from heapq import nlargest
from pathlib import Path
import datetime
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Define a lock for synchronizing access to curID
curID_lock = Lock()

def write_pagelist():
    with open('pagelist.txt','w+') as file:
        for k,v in page_dict.items():
            file.writelines(f"{k}\n")

def load_pagelist():
    page_dict = {}
    with open('pagelist.txt','r') as file:
        for line in file.readlines():
            page = line.rstrip()
            page_dict.update({page:1}) #1 for page visited
    return page_dict

def write_curID(value):
    with open ('current_ID.txt','w+') as file:
        file.write(str(value))

def get_curID():
    with open ('current_ID.txt','r') as file:
        return int(file.readline())



#We load our current ID and list of pages we've already visited
page_dict = {}
curID = get_curID()
page_dict = load_pagelist()

#load database
filepath = 'D:/database/foxnewsDB.db'
try:
    conn = sqlite3.connect(filepath)
    print("Database succesfully opened")
except Error as e:
    print(e)
cursor = conn.cursor()

#cursor.execute("CREATE TABLE news_articles(id INTEGER PRIMARY KEY, link TEXT, insertion_date TIMESTAMP, title TEXT, author TEXT, publication_date TEXT, tag TEXT, content TEXT)")

#These are the sources we use to find articles
single_page_tags = ["news","local-news","national-news"]
multi_page_tags = {"unusual":False,"politics":False,"consumer":False,"entertainment":False,
                   "business":False,"health":False,"viral":False,"us/ga":False,
                    "politics/ga-politics":False,"us/ga/cobb-county":False,"us/ga/dekalb-county":False,
                    "us/ga/fulton-county":False,"us/ga/atlanta":False,"us/ga/gwinnett-county":False,
                    "us/ga/clayton-county":False,"money/us-economy":False,"money":False,"business/personal-finance":False,
                    "series/i-team":False,"series/fox-medical-team":False} #If value is True, we stop searching

def update_DB(url,tag="none"):
    print(f"Now searching:{url}\n")
    #We use this to stop early if we hit a certain number of already stored pages
    already_visited_count = 0

    global curID
    # We get a bs4 object for the webpage
    req = requests.get(url)
    soup = bs4.BeautifulSoup(req.text, "html.parser")


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
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(parse_news, newsList)

    for result in results:
        already_visited_count += result
        if already_visited_count >= 5:
            print("Exceeded max number of already visited pages. Stopping early!")
            if tag != "none":
                multi_page_tags[tag] = True

            return #stop early if we exceed 5 already visited pages

def parse_news(news): #returns 1 for page already visited, 0 otherwise

    global curID
    #We skip a page if it's already been visited
    if(page_dict.get(news) == 1):
        print("Page already stored\n")
        return 1

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

    #Acquire a unique ID for the current worker
    with curID_lock:
        curID += 1
        cur_id = curID

    #We add the entry to our database
    curTime = datetime.datetime.now()
    db_operations.append((curID,news,curTime,title,author,date,keyword,content))
    print("Prepared to add to database!\n")
    page_dict.update({news:1})
    return 0
        
db_operations = [] #List of DB operations to do all at once

for tag in single_page_tags:
    url = "https://www.fox5atlanta.com" + '/' + tag
    update_DB(url)

for tag,bval in multi_page_tags.items(): 
    for i in range (1,9):
        url = "https://www.fox5atlanta.com" + "/tag/" + tag + "?page=" + str(i)
        bval = multi_page_tags[tag]

        if bval:
            print(f"No new articles in {tag}. Continuing.") #Skip to next tag if there's no new articles
            break
        else:
            update_DB(url,tag)
    
# perform all database operations in a single transaction
for operation in db_operations:
    cursor.execute("INSERT into news_articles VALUES(?,?,?,?,?,?,?,?)", operation)

conn.commit()

# All done!
changes = conn.total_changes
conn.close()
write_curID(curID)
write_pagelist()

print(f"Successfully made {changes} changes")
exitvar = input("Done! press any key to exit...")
    



    
