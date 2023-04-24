import streamlit as st
import streamlit.components.v1 as components

import networkx as nx
from pyvis.network import Network

#get NLP libraries
import nltk_download_utils
from nltk.tokenize import sent_tokenize
from newspaper import Article
from newspaper.article import ArticleException
import spacy
import neuralcoref

#get selenium and associated packages
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from time import sleep

#analysis packages
import pandas as pd
import numpy as np

#everything else
from itertools import product
from more_itertools import unique_everseen
import json

#spacy stuff
nlp = spacy.load('en_core_web_sm')
coref = neuralcoref.NeuralCoref(nlp.vocab)
nlp.add_pipe(coref, name='neuralcoref')

st.title('clip-search.ai')

def clip_search(query, count):
    #initialize selenium instance in BrowserStack with below specifications
    desired_cap = {
        'os_version': 'Big Sur',
        'resolution': '1920x1080',
        'browser': 'Chrome',
        'browser_version': 'latest',
        'os': 'OS X',
        'name': 'BStack-[Python] Sample Test', 
        'build': 'BStack Build Number 1'}
    
    driver = webdriver.Remote(command_executor ='http://arisen2:WmX3RxEUQ5bvQjCquLJy@hub-cloud.browserstack.com/wd/hub', desired_capabilities = desired_cap)

    #Go to Google
    driver.get('http://www.google.com')

    #find the search bar
    search_query = driver.find_element_by_name('q')

    #enter the search query and press enter
    search_query.send_keys(query)
    sleep(5)
    search_query.send_keys(Keys.RETURN)

    #make an empty list to store the urls of articles
    news_urls = []

    #Find all the links in the news section and go to those links
    news_section = driver.find_elements_by_class_name('hdtb-mitem')
    counter = 0
    for i in news_section:
        if counter == 1:
            elements = i.find_elements_by_tag_name("a")
            for j in elements:
                x = j.get_attribute("href")
                driver.get(x)
            counter += 1
        else: 
            counter += 1

    #get all the URLs for all the news stories 
    content_blocks = driver.find_elements_by_class_name('ftSUBd')

    for block in content_blocks:
        elements = block.find_elements_by_tag_name("a")
        news_urls = [el.get_attribute("href") for el in elements]

    
    try:
        #try going to the next page of urls to do the same thing, add to the list of urls until you hit the specified count
        while len(news_urls) < count:
            next_button = driver.find_element_by_id('pnnext')
            next_button.click()
            news_section = driver.find_elements_by_class_name('hdtb-mitem')
            counter = 0
            for i in news_section:
                if counter == 1:
                    elements = i.find_elements_by_tag_name("a")
                    for j in elements:
                        x = j.get_attribute("href")
                        driver.get(x)
                    counter += 1
                else: 
                    counter += 1

            content_blocks = driver.find_elements_by_class_name('ftSUBd')

            for block in content_blocks:
                elements = block.find_elements_by_tag_name("a")
                news_urls = [el.get_attribute("href") for el in elements]
            
            sleep(2)
    except:
        pass

    driver.quit()

    #make a list to store our nodes
    nodes = []

    #make a list to store our urls
    urls = []

    #make a to store our sentence and token indicies
    sent_idx = []
    toke_idx = []

    #make lists to store our coreferents, their indicies and their urls
    corefs = []
    coref_idx = []
    urls1 = []

    #loop through each article
    for i in news_urls:
        try:
            #download the text of each article
            article = Article(i)
            article.download()
            article.parse()
            article.nlp()

            #get the full text of the article
            text = article.text

            doc = nlp(text)

            #initialize the tokenizer 
            tokenizer = nlp.tokenizer 

            #split the article into sentences
            sents = sent_tokenize(doc.text)
            
            counter = 0
            
            #loop through each sentence
            for j,k in enumerate(sents):

                #split sentence into words
                x = tokenizer(k) 
                
                sent_idx += len(x) * [j]

                #for each token in the sentence
                for l in x:
                    counter += 1
                    #append the index of the token
                    toke_idx.append((counter - 1))
                    #append the url for the that token
                    urls.append(i)

            #loop through each corefence chain 
            for idx, chain in enumerate(doc._.coref_clusters):
                for mention in chain.mentions:
                    #add the index of the coreference
                    coref_idx.append(idx)
                    #
                    corefs.append(mention.start)
                    urls1.append(i)
                    


            for k, l in enumerate(sents):

                #Use Spacy to extract all the entities from the sentence and them add them to the entities list
                entity = nlp(l)


                for ee in entity.ents:
                    ent_dict = {}

                    #we only want person or organization entities
                    if ee.label_ == 'PERSON':
                        #get the name and clean it up
                        ent_dict['name'] = ee.text.replace('\n',' ').replace("'s'", "").strip()
                        #get the entity type
                        ent_dict['label'] = ee.label_
                        #get the index for the sentence
                        ent_dict['sent_idx'] = k
                        #get the position of the entity
                        ent_dict['start'] = ee.start
                        ent_dict['end'] = ee.end
                        #get the url for that entity
                        ent_dict['urls'] = i
                        #add the node dictionary to our nodes list
                        nodes.append(ent_dict)
                    elif ee.label_ == 'ORG':
                        #get org name and clean it up
                        ent_dict['name'] = ee.text.replace('\n',' ').replace("'s", "").strip()
                        #get entity types
                        ent_dict['label'] = ee.label_
                        #get index of the sentence
                        ent_dict['sent_idx'] = k 
                        #get position of entity (token index)
                        ent_dict['start'] = ee.start
                        ent_dict['end'] = ee.end
                        #get url
                        ent_dict['urls'] = i
                        #add node dict to nodes list
                        nodes.append(ent_dict)
                    else:
                        pass
        except ArticleException:
            pass
    #d is every word in every article we scraped, enumerated with the URL
    d =  {'sent_idx': sent_idx, 'toke_idx': toke_idx, 'urls': urls}

    #e is every coreference chain in every article we scraped with its index and url 
    e = {'toke_idx': corefs, 'coref_idx': coref_idx, 'urls': urls1}
    
    #convert to dataframes
    df = pd.DataFrame(d)
    dfa = pd.DataFrame(e)

    #make a df for our nodes
    dfb  = pd.DataFrame(nodes)

    links = []
    #loop through every unique node url
    for j in set(dfb['urls']):
        #filter to just the nodes for that article
        df1a = dfb.loc[dfb['urls'] == j].copy()
        
        #
        for i in set(df1a['sent_idx']): 
            link = {}
            
            #filter to that sentence
            df1 = df1a.loc[df1a['sent_idx'] == i].copy()
            
            if len(df1) > 1:
                name1 = list(df1['name'])
                name2 = list(df1['name'])

                x = list(product(name1, name2))
                
                #delete links where both nodes are the same
                x = [k for k in x if k[0] !=  k[1]]
                
                #delete reverse tuples
                x = list(unique_everseen(x, key=frozenset))

                #delete links with empty strings
                x = [l for l in x if l[0] != '' and l[1] != ''] 
                
                #if there is nothing left just pass
                if len(x) == 0:
                    pass
                
                #if there is only one edge
                elif len(x) == 1:
                    #specify the origin node
                    source = x[0][0]
                    #specify the target node
                    target = x[0][1]

                    #get the entity types for the origin and target
                    type1 = df1.loc[df1['name'] == source, 'label'].iloc[0]
                    type2 = df1.loc[df1['name'] == target, 'label'].iloc[0]
                    
                    #we dont care about org-org pairs
                    if type1 == 'ORG' and type2 == 'ORG':
                        pass
                    
                    else:
                        #create edge dictionary
                        link['source'] = source
                        link['target'] = target
                        link['type'] = f'{type1}-{type2}'
                    
                    #if we dont already have the edge then add it to our edge list
                    if link not in links:
                            links.append(link)
                    else:
                        pass
                
                else:
                    #if there is more than two entities in that sentence
                    for m in range(0, len(x)):
                        #specify origin node
                        source = x[m][0]
                        #spcify target node 
                        target = x[m][1]
                        #get entity types for both
                        type1 = df1.loc[df1['name'] == source, 'label'].iloc[0]
                        type2 = df1.loc[df1['name'] == target, 'label'].iloc[0]
                        
                        #we don't care about org-org pairs
                        if type1 == 'ORG' and type2 == 'ORG':
                            pass
                        
                        else:
                            #define edge dictionary
                            link['source'] = source
                            link['target'] = target
                            link['type'] = f'{type1}-{type2}'
                        
                        #If that pair isn't already listed, add it.
                        if link not in links:
                            links.append(link)
                        
                        else:
                            pass
                        
            else:
                pass
    
    #Join dataframes to get sentence index for coreferents      
    df = pd.merge(df, dfa, how='inner', on=['toke_idx', 'urls'])


    for i in set(urls):
        #filter the index df and coreferent df to just that article
        df2a = df.loc[df['urls'] == i].copy()
        df3a = dfb.loc[df['urls'] == i].copy()

        #get the sentence index of every token with the same coref_idx
        for j in set(df2a['coref_idx']):
            df2 = df2a.loc[df2a['coref_idx'] == j]

            #grab all the entities from all of the coref sentences
            if len(set(df2['sent_idx'])) > 1:
                link  = {}
                coref_sents = list(set(df2['sent_idx']))
                df3 = df3a[df3a['sent_idx'].isin(coref_sents)].copy()
                
                name1 = list(df3['name'])
                name2 = name1

                #generate all possible pairs
                x = list(product(name1, name2))

                #delete links where both nodes are the same
                x = [k for k in x if k[0] !=  k[1]] 
                
                #delete reverse tuples
                x = list(unique_everseen(x, key=frozenset))

                #delete links with empty strings
                x = [l for l in x if l[0] != '' and l[1] != ''] 
                
                #if there are no edges then pass
                if len(x) == 0:
                    pass
                
                #if there is one edge wire it up in the same way
                elif len(x) == 1:
                    source = x[0][0]
                    target = x[0][1]
                    type1 = df3.loc[df3['name'] == source, 'label'].iloc[0]
                    type2 = df3.loc[df3['name'] == target, 'label'].iloc[0]
                    
                    if type1 == 'ORG' and type2 == 'ORG':
                        pass
                    else:
                        link['type'] = f'{type1}-{type2}'
                        link['target'] = x[0][1]
                        link['source'] = x[0][0]
                    
                    if link not in links:
                            links.append(link)
                    else:
                        pass
                
                else:
                    pass

    #delete empty edge dicts
    links = [link for link in links if link != {}]

    #make our edges into a dict
    links_df = pd.DataFrame(links)

    return links_df

#initialize a Streamlit form
with st.form("form"):
    #have user input a search query
    query_val = st.text_input("Enter your search query here:")
    #have user input how many articles they want to scrape
    count_val = st.number_input("How many articles do you want to scrape?", min_value=10, max_value=200, step=10)
    #create a submit button
    submitted = st.form_submit_button("Submit")

    #when they click submit
    if submitted:
        #run the function
        links = clip_search(query_val, count_val)
        
        #create our dynamic knowledge graph using NetworkX
        G = nx.from_pandas_edgelist(links, 'source', 'target')

        net = Network(height='600px', bgcolor='#222222', font_color='white')

        net.from_nx(G)

        net.repulsion(node_distance=420, central_gravity=0.33,
                            spring_length=110, spring_strength=0.10,
                            damping=0.95)


        try:
            #load the html for the knowledge graph on the page
            path = '/tmp'
            net.save_graph(f'{path}/pyvis_graph.html')
            HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

        except:
            #if for some reason it doesn't load, save it as a file
            path = '/html_files'
            net.save_graph(f'{path}/pyvis_graph.html')
            HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

        components.html(HtmlFile.read(), height=600, width=600)