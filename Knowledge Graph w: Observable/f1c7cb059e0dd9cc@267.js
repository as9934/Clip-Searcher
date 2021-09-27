// https://observablehq.com/@as9934/a-force-directed-knowledge-graph-from-scraped-news-article/3@267
export default function define(runtime, observer) {
  const main = runtime.module();
  const fileAttachments = new Map([["entities@2.json",new URL("./files/1d6c549123592325cfef7ebed8de233ab0b662f54b4fa6687b5e39754e902e6a5d1304c07743bae2225a454b6a18291717283c3a74a1e0de9dfc114d85bd4f32",import.meta.url)]]);
  main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
  main.variable(observer()).define(["md"], function(md){return(
md` <h1>A Force-Directed Knowledge Graph from Scraped News Articles</h1><br><strong>By:</strong><em> Ari Sen</em>`
)});
  main.variable(observer("chart")).define("chart", ["data","d3","width","height","color","drag","invalidation"], function(data,d3,width,height,color,drag,invalidation)
{
  //Create each node and link
  const links = data.links.map(d => Object.create(d));
  const nodes = data.nodes.map(d => Object.create(d));

  //define our force simulation
  const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id))
      //spread the node aprt from eachother so they can be read
      .force("charge", d3.forceManyBody().strength(-150))
      .force("collide",d3.forceCollide().radius(d => d.r * 10))
      //put the center node in the center
      .force("center", d3.forceCenter(width / 2, height / 2));

  //Make an  SVG
  const svg = d3.create("svg")
      .attr("viewBox", [0, 0, width, height]);
  
  //add the links between each node
  const link = svg.append("g")
      //make the links gray and semi-opaque
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.7)
    .selectAll("line")
    .data(links)
    .join("line")
      //set the link length
      .attr("stroke-width", d => Math.sqrt(d.value));

  // create nodes
  const node = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1)
    .selectAll("circle")
    .data(nodes)
    .join("circle")
      // give each node a radius of 10
      .attr("r", 10)
      // set the color on a scale based on the group
      .attr("fill", color)
      //initiate the force simulation
      .call(drag(simulation));
  
  // add the labels
  const textElements = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .enter().append('text')
      .text(node => node.id)
      //set font size at 10
      .attr('font-size', 10)
      .attr('dx', 10)
      .attr('dy', 5)
  
  //when you mouseover a node:
  node.on('mouseover', function (d) {
    // change its color to red
    d3.select(this).style('fill', "firebrick")
    
    //change its link color to black 
    link
      .style('stroke', function (link_d) { return link_d.source === d.id || link_d.target === d.id ? 'firebrick' : 'black';})
      .style('stroke-width', function(link_d) { return link_d.source === d.id || link_d.target === d.id ? 4 : 1;})
  });
  
  //when you mouseout, revert to the settings we had before
  node.on('mouseout' , function(d) {
    node.style("fill", color)
    link.style("stroke", "#999")
    link.style("stroke-opacity", 0.7)
    link.style("stroke-width", d => Math.sqrt(d.value))
  });
    
  //for each link, node and tetx element, move with the force direction
  simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    textElements
        .attr("x", node => node.x)
        .attr("y", node => node.y)
  });

  invalidation.then(() => simulation.stop());

  return svg.node();
}
);
  main.variable(observer()).define(["md"], function(md){return(
md`<h2>Writeup</h2>
<u><strong>Context</strong></u>
<p>One of the most time-consuming task in investigative reporting is the "clip search."  This is where you scour the internet in search of articles related to the topic you are writing on to make sure you aren't re-writing the same story. This isn't always 100 percent possible. But when it isn't, you want to give credit where credit is due.</p>
<p>The other benefit of this process is that you start to notice connections between people involved in a story: the experts who are constantly quoted, the people surrounding your person/topic of interest and the activists or advocacy organizations who are most against them/it. Traditional methods for storing this information like Word/Google documents or Excel spreadsheets often don't do a good job mapping these relationships, which can be a major issue down the line when it comes time to write.</p>
<p> During a recent clip search I noticed that much of this process is highly repetitve: read article then input headline, url, publication date and summary into spreadsheet. My experience with programming has taught me that highly repetitive tasks are usually the easiest to automate, so I set off trying to do just that.</p>
<p> Using some natural  lanaguage processing libraries in Python I found it was relatively straightforward to extract some of the common things I was pulling out, including the url, headline, bylines, publication date from a news article. I was even able to generate a halfway decent summary using PyTorch and the pretrained Hugging Face T5 transformer library. But what about the relationships?</p>
<p>To address that issue I decided to create a "knowledge graph" of names. In laymans terms this simply means I wanted to created a diagram which showed the relationships between different people. My operating assumptions were:
<ol>
<li>That if two names showed up in the same news article, there was a very good chance that they were related in some way and </li>
<li>That if the same name showed up multiple times across various news articles, they were likely important to the topic.</li>
</ol> 
<u><strong>Data</strong></u>
<p> I wanted to take a different approach when in came to data. I didn't just wanted to download something from Kaggle or data.world (though that probably would have been easier). I wanted to use news articles which were directly related to something I'm currently working on. </p>
<p> For the past few months I've been investigating the increase in the use of surveillance technology on college campuses post-Charlottesville. In my research on the subject one company kept coming up: Social Sentinel. So I decided to create a knowledge graph of news articles which contained "Social Sentinel" and either "college" or "university". To keep things reasonable I decided to only use the first 20 articles on the subject, although in the future this could certainly be expanded.</p>
<p>The first step was to write a Python web scraper with Selenium to input the search query into Google and then grab the text of the first 20 news articles that came up. This was pretty simple, as I had done a very similar process for another project before. The next step was to search through the text of the articles to find all of the names. For this I used Spacy, which makes this "entity extraction" process incredibly simple. I then wanted to verify each of the things Spacy pulled out to make sure it actually was a name and not just a capitalized word. To do this I wrote code which would only pull out the entities with spaces in them (to get only full names) and then looped through all the remaining entities and allowed the user (in this case me) to type "y" if the entity was indeed a full name. If it was approved, the name was stored in a list for use later.</p>
<p> I knew the next step was to get the data into a JSON format so it could be used by the D3 visualization. In particular, after taking a look at some examples, I knew that I had to create a section which housed each "node" or name and their "group" or URL and another section which showed the relationship between all of these nodes. To accomplish this I created two text files in Python "nodes.txt" and "links.txt" where this information could be written and then looped through each name so it could be plugged into a string. For the "links" file, I used the permutation function in itertools to make sure that every name in a given article was linked to every other name in that article. These two text files were then combined into one file called entities.txt which I simply copied into VS Code and saved as a JSON. After a tiny bit of cleaning, I uploded that JSON to this Observable notebook.</p>
`
)});
  main.variable(observer()).define(["md"], function(md){return(
md`
<h2><u>Python Code</u></h2>
    #get NLP libraries
    import nltk 
    from newspaper import Article

    import spacy

    #get selenium and associated packages
    from selenium import webdriver
    from selenium.webdriver import Chrome
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options

    #everything else
    import json
    import os
    from itertools import permutations
    from IPython.display import clear_output

    #set selenium options to headless
    options = Options()
    options.headless = True
    #path to your chromedriver
    driver = webdriver.Chrome('~/chromedriver', chrome_options=options) 

    #go to google
    driver.get('https://www.google.com')

    #input your search query
    search_query = driver.find_element_by_name('q')

    search_query.send_keys('"Social Sentinel" AND "college" OR "university"')
    search_query.send_keys(Keys.RETURN)

    #go to the news section

    news_section = driver.find_element_by_class_name('hide-focus-ring').click()

    more_results = driver.current_url + '&num=20'
    driver.get(more_results)

    #store all the urls

    news_urls = []

    content_blocks = driver.find_elements_by_class_name("dbsr")

    for block in content_blocks:
        elements = block.find_elements_by_tag_name("a")
        for el in elements:
            news_urls.append(el.get_attribute("href"))

    #make empty lists
    headlines = []
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

    #loop through all the urls

    for i in news_urls:
        try: 
            article = Article(i)
            article.download()
            article.parse()
            article.nlp()

            text = article.text

            #Use Spacy to extract all the names from the full text of the article and add them to the ent list
            nlp = spacy.load('en_core_web_sm')
            entity = nlp(text)
            people = [str(ee) for ee in entity.ents if ee.label_ == 'PERSON']

            #for each url we only want to have a name appear once, so we are creating a list INSIDE of our loop
            persons = []

            #for each thing spacy thinks is a person's name
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

    # Merging two files into one file 
    data += "\n"
    data += data2 

    with open ('entities.txt', 'w') as fp: 
        fp.write(data)
  `
)});
  main.variable(observer()).define(["md"], function(md){return(
md `<h2> <u>Boilerplate D3 Stuff</u> </h2>`
)});
  main.variable(observer("d3")).define("d3", ["require"], function(require){return(
require("d3@6")
)});
  main.variable(observer("data")).define("data", ["FileAttachment"], function(FileAttachment){return(
FileAttachment("entities@2.json").json()
)});
  main.variable(observer("color")).define("color", ["d3"], function(d3)
{
  const scale = d3.scaleOrdinal(d3.schemeCategory10);
  return d => scale(d.group);
}
);
  main.variable(observer("height")).define("height", function(){return(
800
)});
  main.variable(observer("width")).define("width", function(){return(
1200
)});
  main.variable(observer("drag")).define("drag", ["d3"], function(d3){return(
simulation => {
  
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }
  
  function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }
  
  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }
  
  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}
)});
  return main;
}
