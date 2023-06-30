import os, sys, bs4, requests, webbrowser, re, spacy
from heapq import nlargest
from pathlib import Path
from datetime import date

# We get our news from here
url = "https://www.fox5atlanta.com/news" 

# We create a file name which includes today's date
currentDate = str(date.today())  
filename = Path.cwd()/'Summaries'/f'News_{currentDate}.txt'
sumFile = open(Path.cwd()/'Summaries'/f'News_{currentDate}.txt','w+')

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
    sumFile.write(news)
    req = requests.get(news)
    soup = bs4.BeautifulSoup(req.text,"html.parser")

    # We assign the article text into a variable called content
    article = soup.find('div',class_="article-body")
    paragraphs = article.find_all('p')
    content = ' '.join([paragraph.get_text(strip=True) for paragraph in paragraphs])

    # Process the text with SpaCy
    doc = nlp(content)

    sentence_scores = {}
    for sent in doc.sents:
        score = 0
        for token in sent:
            if token.is_alpha and not token.is_stop:
                score += token.norm_.count(" ") + 1
                sentence_scores[sent] = score

    # Choose the number of sentences for the summary
    num_sentences = 5

    # Select the top N highest-scoring sentences
    top_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)

    # Combine the top sentences to create the summary
    summary = ' '.join([sent.text for sent in top_sentences])

    # We now output summary to console and also write to our summary file
    print(summary)

    sumFile.write('\n')
    sumFile.write(summary.replace('.','.\n'))
    print("\n\n\n")
    sumFile.write("\n\n\n")

# All done!
sumFile.close()
exitvar = input("Done! press any key to exit...")
    



    
