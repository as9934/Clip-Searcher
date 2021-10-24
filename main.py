
#get flask
from flask import Flask
from flask import request
from flask import escape

#for mapping nodes and links in the JSON file
from itertools import permutations
from newspaper.article import ArticleException

#get NLP libraries
#nltk and newspaper for headline, byline, pub date, extractive summary and text
import nltk 
from newspaper import Article

#spacy for entity extraction
import spacy

#pytorch and T5 transformer for abstractive summarization
import torch
import json 
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config

#get selenium and associated packages
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

#get pandas
import pandas as pd
import pygsheets

app = Flask(__name__)

@app.route("/")
def index():
    query = request.args.get("query", "")
    if query:
        g_url = clip_search(query)
    else: 
        g_url = ""
    return (
        """<form action="" method="get">
                Query: <input type="text" name="query">
                <input type="submit" value="Get Google Sheet URL">
            </form>"""
        + "URL: "
        + g_url
    )

def clip_search(query):
    desired_cap = {
 'os_version': 'Big Sur',
 'resolution': '1920x1080',
 'browser': 'Chrome',
 'browser_version': 'latest',
 'os': 'OS X',
 'name': 'BStack-[Python] Sample Test', # test name
 'build': 'BStack Build Number 1' # CI/CD job or build name
}
    
    driver = webdriver.Remote(command_executor ='http://arisen2:WmX3RxEUQ5bvQjCquLJy@hub-cloud.browserstack.com/wd/hub', desired_capabilities = desired_cap)
    
    driver.get('http://www.google.com')

    search_query = driver.find_element_by_name('q')

    search_query.send_keys(query)
    search_query.send_keys(Keys.RETURN)

    news_section = driver.find_element_by_class_name('hdtb-mitem').click()

    more_results = driver.current_url + '&num=200'
    driver.get(more_results)

    news_urls = []

    content_blocks = driver.find_elements_by_class_name("ftSUBd")

    for block in content_blocks:
        elements = block.find_elements_by_tag_name("a")
        for el in elements:
            news_urls.append(el.get_attribute("href"))

    #quit the driver
    driver.quit()

    #make lists for headlines, bylines, publish dates, summaries and entites
    headlines = []
    bylines = []
    pub_dates = []
    summaries = []
    ab_summaries = []
    entities_list = []
    people_list = []

    #create two new text files where your nodes and edges will be stored
    nodes = open("nodes.txt", "w")
    nodes.write('{')
    nodes.write('\n')
    nodes.write('\t')
    nodes.write('"nodes":[')
    nodes.write('\n')


    links = open("links.txt", "w")
    links.write('\t')
    links.write('"links":[')
    links.write('\n')

    #for every URL in the news_urls list
    for i in news_urls: 
        try:

            #convert the url into an article with the newspaper package, download it and run the NLP
            article = Article(i)
            article.download()
            article.parse()
            article.nlp()
        except: 
            pass

        try:
            #get the headline, bylines, publish dates and summaries and add them to their respective lists
            headline = article.title
            headlines.append(headline)
        except: 
            headline.append('n/a')
            pass

        try:

            byline = article.authors
            bylines.append(byline)

        except:

            bylines.append('n/a')
            pass

        try:

            pub_date = article.publish_date
            pub_dates.append(pub_date)

        except:
            pub_dates.append('n/a')
            pass

        try:

            summary = article.summary
            summaries.append(summary)

        except: 
            summaries.append('n/a')
            pass

        #get the full text of the article
        text = article.text

        try:
            #Use Spacy to extract all the entities from the full text of the article and them add them to the entities list
            nlp = spacy.load('en_core_web_sm')
            entity = nlp(text)
            entities = entity.ents
            entities_list.append(entities) 
            #find all the entities Spacy thinks are people
            people = [str(ee) for ee in entity.ents if ee.label_ == 'PERSON']
            persons = []
            #for each thing spacy thinks is a persons name
            for l in people:
                #we only want full names so only display names with spaces
                if ' ' in l:
                    #give the user approval over what is a name and what isn't
                    print(f'Is {l} a persons full name? If yes, type "y"')
                    x = input()
                    if x == 'y':
                        #strip all the whitespace
                        l = l.strip()
                        #as stated before we only want the same person once per url
                        if l not in persons:
                            persons.append(l)
                        else:
                            pass
                        #store all the unique names for each url in the list we created outside of the loop
                        for m in persons:
                            people_list.append(m)
                        
                        #make each node for a particular url point to every other node in that url
                        perm = permutations(persons, 2)
                        
                        for j in list(perm):
                            perms = list(j)
                            links.write('\t')
                            links.write('\t')
                            links.write('{"source": ' + f'"{perms[0]}", "target": ' + f'"{perms[1]}", "value": ' + f'"{i}"' + '},')
                            links.write('\n')
                    else:
                        pass
                else:
                    pass
            #create every node
            for k in people_list:
                nodes.write('\t')
                nodes.write('\t')
                nodes.write('{"id": ' + f'"{k}"' + ', ' +  f'"group": "{i}"' + '},')
                nodes.write('\n')
    
        except ArticleException:
            entities_list.append(['n/a'])
            pass
        
        #write the end of the txt files, which will become JSON
        nodes.write('\t')
        nodes.write('],')
        nodes.write('\n')

        links.write('\t')
        links.write(']')
        links.write('\n')
        links.write('}')

        #close both txt files    
        nodes.close()
        links.close()

        # code to merge the two files
        data = data2 = "" 

        # Reading data from first file 
        with open('nodes.txt') as fp: 
            data = fp.read() 
        with open('links.txt') as fp: 
            data2 = fp.read() 

        # Merging two files into one another file 
        data += "\n"
        data += data2 

        with open ('entities.txt', 'w') as fp: 
            fp.write(data)

        try:
            #Use T5 to generate absstractive summaries
            model = T5ForConditionalGeneration.from_pretrained('t5-small')
            tokenizer = T5Tokenizer.from_pretrained('t5-small')
            device = torch.device('cpu')

            preprocess_text = text.strip().replace("\n","")
            if len(preprocess_text) > 512: 
                preprocess_text = preprocess_text[:512]
            t5_prepared_Text = preprocess_text

            tokenized_text = tokenizer.encode(t5_prepared_Text, return_tensors="pt").to(device)

            summary_ids = model.generate(tokenized_text,
                                                num_beams=4,
                                                no_repeat_ngram_size=2,
                                                min_length=30,
                                                max_length=100,
                                                early_stopping=True)

            output = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            ab_summaries.append(output)
        except:
            ab_summaries.append('n/a')
            pass

    

    #create a spreadsheet by combining the various lists as columns and set the column names
    df = pd.DataFrame(list(zip(headlines, news_urls, bylines, pub_dates, summaries, entities_list, ab_summaries)),columns =['Headline', 'URL', 'Byline(s)', 'Date Published', 'Key Sentences', 'Entities', 'Summary'])

    x = #your google sheets api stuff goes here

    y = json.dumps(x)

    gc = pygsheets.authorize(client_secret=y)

    sh = gc.open('Clip Search')


    sh.share('', role='reader', type='anyone')

    wk1 = sh.sheet1

    wk1.set_dataframe(df, 'A1')

    g_url = wk1.url

    return g_url
        


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
