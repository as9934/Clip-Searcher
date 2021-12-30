
import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network

#get NLP libraries
import nltk
from nltk.tokenize import sent_tokenize
from newspaper import Article
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

#set header
st.title('clip-search.ai')

def clip_search(query, count):
    desired_cap = {
        'os_version': 'Big Sur',
        'resolution': '1920x1080',
        'browser': 'Chrome',
        'browser_version': 'latest',
        'os': 'OS X',
        'name': 'BStack-[Python] Sample Test', 
        'build': 'BStack Build Number 1'}
    
    driver = webdriver.Remote(command_executor ='http://arisen2:WmX3RxEUQ5bvQjCquLJy@hub-cloud.browserstack.com/wd/hub', desired_capabilities = desired_cap)
    
    graph = {}

    driver.get('http://www.google.com')

    search_query = driver.find_element_by_name('q')

    search_query.send_keys(query)
    sleep(5)
    search_query.send_keys(Keys.RETURN)

    news_urls = []

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
        for el in elements:
            news_urls.append(el.get_attribute("href"))


    try:
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
                for el in elements:
                    news_urls.append(el.get_attribute("href"))
            sleep(5)
    except:
        pass

    driver.quit()

    ##Entity extraction 

    #for each entity we need the entity type (person or org), the sentence index, the word index, the article its in, coreference chain 

    nodes = []

    urls = []
    sent_idx = []
    toke_idx = []

    corefs = []
    coref_idx = []
    urls1 = []
    for i in range(0, len(news_urls)):
        try:
            article = Article(news_urls[i])
            entities = []
            article.download()
            article.parse()
            article.nlp()


            #get the full text of the article
            text = article.text

            doc = nlp(text)

            tokenizer = nlp.tokenizer 

            sents = sent_tokenize(doc.text)
            
            counter = 0
            
            for j,k in enumerate(sents):

                x = tokenizer(k) #split sent into words
                
                sent_idx += len(x) * [j]

                for l in x:
                    counter += 1
                    toke_idx.append((counter - 1))
                    urls.append(news_urls[i])
        
            

            
            for idx, chain in enumerate(doc._.coref_clusters):
                for mention in chain.mentions:
                    coref_idx.append(idx)
                    corefs.append(mention.start)
                    urls1.append(news_urls[i])
                    


            for k, l in enumerate(sents):

                #Use Spacy to extract all the entities from the sentence and them add them to the entities list
                entity = nlp(l)


                for ee in entity.ents:
                    ent_dict = {}
                    #we only want person or organization entities
                    if ee.label_ == 'PERSON':
                        ent_dict['name'] = ee.text.replace('\n',' ').replace("’s'", "").strip()
                        ent_dict['label'] = ee.label_
                        ent_dict['sent_idx'] = k
                        ent_dict['start'] = ee.start
                        ent_dict['end'] = ee.end
                        ent_dict['urls'] = news_urls[i]
                        nodes.append(ent_dict)
                    elif ee.label_ == 'ORG':
                        ent_dict['name'] = ee.text.replace('\n',' ').replace("’s", "").strip()
                        ent_dict['label'] = ee.label_
                        ent_dict['sent_idx'] = k 
                        ent_dict['start'] = ee.start
                        ent_dict['end'] = ee.end
                        ent_dict['urls'] = news_urls[i]
                        nodes.append(ent_dict)
                    else:
                        pass
        except:
            pass

    d =  {'sent_idx': sent_idx, 'toke_idx':toke_idx, 'urls':urls}
    e = {'toke_idx':corefs, 'coref_idx': coref_idx, 'urls':urls1}
    df = pd.DataFrame(d)
    dfa = pd.DataFrame(e)
    dfb  = pd.DataFrame(nodes)

    dfb

    # links = []
    # for j in list(set(dfb['urls'])):
    #     df1a = dfb.loc[dfb['urls'] == j]
    #     for i in list(set(df1a['sent_idx'])): #filter to that sentence
    #         link = {}
    #         df1 = df1a.loc[df1a['sent_idx'] == i]
    #         if len(df1) > 1:
    #             name1 = df1['name']
    #             name2 = df1['name']
    #             x = product(name1, name2)
    #             x = list(x)
    #             x = [k for k in x if k[0] !=  k[1]] #delete links where both nodes are the same
    #             x = list(unique_everseen(x, key=frozenset)) #delete reverse tuples
    #             x = [l for l in x if l[0] != '' and l[1] != ''] #delete links with empty strings
                
    #             if len(x) == 0:
    #                 pass
    #             elif len(x) == 1:
    #                 source = x[0][0]
    #                 target = x[0][1]
    #                 type1 = df1.loc[df1['name'] == source, 'label'].iloc[0]
    #                 type2 = df1.loc[df1['name'] == target, 'label'].iloc[0]
                    
    #                 if type1 == 'ORG' and type2 == 'ORG':
    #                     pass
    #                 else:
    #                     link['source'] = source
    #                     link['target'] = target
    #                     link['type'] = f'{type1}-{type2}'
                    
    #                 if link not in links:
    #                         links.append(link)
    #                 else:
    #                     pass
    #             else:
    #                 for m in range(0, len(x)):
    #                     source = x[m][0]
    #                     target = x[m][1]
    #                     type1 = df1.loc[df1['name'] == source, 'label'].iloc[0]
    #                     type2 = df1.loc[df1['name'] == target, 'label'].iloc[0]
    #                     if type1 == 'ORG' and type2 == 'ORG':
    #                         pass
    #                     else:
    #                         link['source'] = source
    #                         link['target'] = target
    #                         link['type'] = f'{type1}-{type2}'
                        
    #                     if link not in links:
    #                         links.append(link)
    #                     else:
    #                         pass
                        
    #         else:
    #             pass
            
    # df = pd.merge(df, dfa, how='inner', on=['toke_idx', 'urls']) #to get sent index for corefs 

    # for i in set(urls):
    #     df2a = df.loc[df['urls'] == i]
    #     df3a = dfb.loc[df['urls'] == i]
    #     #get the sent_idx of every token with the same coref_idx
    #     for j in set(df2a['coref_idx']):
    #         df2 = df2a.loc[df2a['coref_idx'] == j]
    #         if len(set(df2['sent_idx'])) > 1:
    #             link  = {}
    #             coref_sents = list(set(df2['sent_idx']))
    #             df3 = df3a[df3a['sent_idx'].isin(coref_sents)]
    #             name1 = list(df3['name'])
    #             name2 = name1
    #             x = list(product(name1, name2))
    #             x = [k for k in x if k[0] !=  k[1]] #delete links where both nodes are the same
    #             x = list(unique_everseen(x, key=frozenset)) #delete reverse tuples
    #             x = [l for l in x if l[0] != '' and l[1] != ''] #delete links with empty strings
                
    #             if len(x) == 0:
    #                 pass
                
    #             elif len(x) == 1:
    #                 source = x[0][0]
    #                 target = x[0][1]
    #                 type1 = df3.loc[df3['name'] == source, 'label'].iloc[0]
    #                 type2 = df3.loc[df3['name'] == target, 'label'].iloc[0]
                    
    #                 if type1 == 'ORG' and type2 == 'ORG':
    #                     pass
    #                 else:
    #                     link['type'] = f'{type1}-{type2}'
    #                     link['target'] = x[0][1]
    #                     link['source'] = x[0][0]
                    
    #                 if link not in links:
    #                         links.append(link)
    #                 else:
    #                     pass
    #             else:
    #                 pass
    # links = [link for link in links if link != {}]

    # links_df = pd.DataFrame(links)

    # return links_df


x = st.text_input("Enter the search term:")
num = st.number_input('Number of Articles to Search:', min_value=10, max_value=200, step=10)

links = clip_search(x, num)

G = nx.from_pandas_edgelist(links, 'source', 'target')

net = Network(height='800px', bgcolor='#222222', font_color='white')

net.from_nx(G)

net.repulsion(node_distance=420, central_gravity=0.33,
                       spring_length=110, spring_strength=0.10,
                       damping=0.95)

# Save and read graph as HTML file (on Streamlit Sharing)
try:
    path = '/tmp'
    drug_net.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

# Save and read graph as HTML file (locally)
except:
    path = '/html_files'
    drug_net.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

# Load HTML file in HTML component for display on Streamlit page
components.html(HtmlFile.read(), height=800)

st.markdown(
"""
<br>
<h6>Created by Arijit (Ari) D. Sen.</h6>
""", unsafe_allow_html=True
)
