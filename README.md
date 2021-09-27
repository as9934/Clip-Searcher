# Clip-Searcher
Flask app which scrapes articles then: <ol>
  <li>Extracts the headline, url, byline and publish date from the article using the Article package built on NLTK</li>
  <li>Summarizes the article  with a T5 Transformer and PyTorch</li>
  <li>Generates a Google sheet with pygsheets where the summaries and extracts are stored </li>
  <li>Generates a JSON file which can be used by D3 to create an interactive knowledge graph of names in the articles.</li>
</ol>
In addition to the files in this repo you will need your own google sheets api key. If you want to deploy to Google Cloud you will need a client secret json and txt file and a credentials json file.

## Context

One of the most time-consuming task in investigative reporting is the "clip search." This is where you scour the internet in search of articles related to the topic you are writing on to make sure you aren't re-writing the same story. This isn't always 100 percent possible. But when it isn't, you want to give credit where credit is due.

The other benefit of this process is that you start to notice connections between people involved in a story: the experts who are constantly quoted, the people surrounding your person/topic of interest and the activists or advocacy organizations who are most against them/it. Traditional methods for storing this information like Word/Google documents or Excel spreadsheets often don't do a good job mapping these relationships, which can be a major issue down the line when it comes time to write.

During a recent clip search I noticed that much of this process is highly repetitve: read article then input headline, url, publication date and summary into spreadsheet. My experience with programming has taught me that highly repetitive tasks are usually the easiest to automate, so I set off trying to do just that.

Using some natural lanaguage processing libraries in Python I found it was relatively straightforward to extract some of the common things I was pulling out, including the url, headline, bylines, publication date from a news article. I was even able to generate a halfway decent summary using PyTorch and the pretrained Hugging Face T5 transformer library. But what about the relationships?

To address that issue I decided to create a "knowledge graph" of names. In laymans terms this simply means I wanted to created a diagram which showed the relationships between different people. My operating assumptions were:
<ol>
    <li>That if two names showed up in the same news article, there was a very good chance that they were related in some way and</li>
    <li>That if the same name showed up multiple times across various news articles, they were likely important to the topic.</li>
</ol>
