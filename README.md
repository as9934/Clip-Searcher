# Clip Searcher

Clip Searcher is a tool that helps journalists and researchers discover hidden connections between people and organizations in the news. Give it a topic, and it will find recent articles, extract the names of people and organizations mentioned, and draw an interactive map showing how they're all connected.

## Why This Exists

One of the most tedious parts of investigative reporting is the "clip search"—combing through dozens of news articles to understand who the key players are in a story and how they relate to each other. Journalists typically track this information in spreadsheets, but those flat lists don't capture the web of relationships that often matter most.

This tool automates that process. It reads news articles and figures out which people and organizations appear together in the same sentences. When two names show up together repeatedly, that's usually a sign they're connected in some meaningful way—maybe one works for the other, or they're opponents in a policy debate, or they're frequently quoted together as experts.

The result is an interactive diagram where you can see, at a glance, the network of relationships in any topic you're researching.

## How It Works

The tool is organized into five Jupyter notebooks, each handling a different step of the process. You can run them individually to understand each piece, or use the final orchestration notebook to run everything at once.

## 1. Scraping (`1_scraping.ipynb`)

This notebook finds and downloads news articles about your topic. It uses DuckDuckGo's news search to find relevant URLs, then downloads the full text of each article. The articles are saved locally so you don't have to re-download them if you want to experiment with different analysis settings later.

## 2. Natural Language Processing (`2_nlp_processing.ipynb`)

This is where the tool reads through each article and identifies the people and organizations mentioned. It uses a technique called "named entity recognition" to spot names in the text—distinguishing between, say, "Apple" the company and "apple" the fruit based on context.

The notebook also performs "coreference resolution," which is a fancy way of saying it figures out when different words refer to the same person. For example, if an article says "President Biden announced the policy. He said it would help families," the tool understands that "He" refers to "President Biden." This helps capture connections that would otherwise be missed.

## 3. Graph Building (`3_graph_building.ipynb`)

Once we know which people and organizations appear in each article, this notebook figures out the connections between them. The rule is simple: if two names appear in the same sentence (or are linked by coreference), they're probably related somehow.

The notebook creates "edges"—lines connecting related entities—and keeps track of what type of connection each one represents (person-to-person, person-to-organization, etc.).

## 4. Visualization (`4_visualization.ipynb`)

This notebook takes all those connections and draws them as an interactive network diagram. People are shown in green, organizations in blue, and you can click and drag nodes around to explore the relationships. Hovering over a node shows you more details about that person or organization.

## 5. Full Pipeline (`5_orchestration.ipynb`)

This notebook runs the entire process from start to finish with a single click. Enter your search topic and the number of articles you want to analyze, and it handles the rest. It also includes an optional web interface (using a tool called Gradio) that makes it easy to run searches without touching any code.

## Getting Started

This project uses `uv` for dependency management. To set it up:

```bash
# Install dependencies
uv sync

# Install required language models (run after each uv sync)
uv pip install "en_core_web_lg @ https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0.tar.gz"
uv pip install "https://github.com/richardpaulhudson/coreferee/raw/master/models/coreferee_model_en.zip"

# Launch Jupyter to run the notebooks
uv run jupyter lab
```

## Project Structure

```
├── analysis/           # Jupyter notebooks for each pipeline step
├── data/raw/          # Downloaded articles and generated outputs
├── Earlier Versions/  # Original implementation files
├── pyproject.toml     # Project dependencies
└── README.md          # This file
```

---

## Disclosure

The original code for this project was written by Ari Sen. It was subsequently refactored by Claude Opus 4.5 (Anthropic) in January 2026 to use modern Python packaging with `uv`, reorganize the code into modular Jupyter notebooks, and replace browser-based scraping with the simpler DuckDuckGo search API.

This README was written by Claude Opus 4.5.
