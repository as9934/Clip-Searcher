# Clip Searcher
Streamlit app which scrapes articles on a given topic then: <ol>
  <li>Extracts person and organizations entities</li>
  <li>Extracts all coreferences for these entities</li>
  <li>Indexes every sentence and token</li>
  <li>Maps relationships between these entities in an interatcive knowledge graph.</li> 
</ol>


## Context

One of the most time-consuming task in investigative reporting is the "clip search." This is where you scour the internet in search of articles related to the topic you are writing on to make sure you aren't re-writing the same story. This isn't always 100 percent possible. But when it isn't, you want to give credit where credit is due.

The other benefit of this process is that you start to notice connections between people involved in a story: the experts who are constantly quoted, the people surrounding your person/topic of interest and the activists or advocacy organizations who are most against them/it. Traditional methods for storing this information like Word/Google documents or Excel spreadsheets often don't do a good job mapping these relationships, which can be a major issue down the line when it comes time to write.

During a recent clip search I noticed that much of this process is highly repetitve: read article then input headline, url, publication date and summary into spreadsheet. My experience with programming has taught me that highly repetitive tasks are usually the easiest to automate, so I set off trying to do just that.


To address that issue I decided to create a "knowledge graph" of names. In laymans terms this simply means I wanted to created a diagram which showed the relationships between different people. My operating assumption was:
<ul>
    <li>That if a person, or its coreferent, shows up in the same sentence with an organization or another person in the same news article, there was a very good chance that they were related in some way</li>
</ul>
