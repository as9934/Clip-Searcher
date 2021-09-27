# Clip-Searcher
Flask app which scrapes articles then: 1. extracts headline, url, byline and publish date 2. summarizes the article and 3. generates a Google sheet where the summaries and extracts are stored and 4.generates a JSON file which can be used by D3 to create an interactive knowledge graph of names in the articles.

In addition to the files in this repo you will need your own google sheets api key. If you want to deploy to Google Cloud you will need a client secret json and txt file and a credentials json file.
