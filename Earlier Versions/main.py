"""
Clip-Search.ai - Entity Relationship Graph Generator

A Streamlit application that scrapes news articles, extracts named entities,
resolves coreferences, and visualizes entity relationships as an interactive graph.

This main module orchestrates the pipeline using modular components:
- Scraping: Web scraping with Selenium and newspaper4k
- NLP Processing: Entity extraction and coreference resolution with spaCy and Coreferee
- Graph Building: Relationship graph construction
- Visualization: Interactive graph rendering with PyVis
"""

import streamlit as st
import streamlit.components.v1 as components

import networkx as nx
from pyvis.network import Network

# NLP libraries
import spacy
import coreferee
from nltk.tokenize import sent_tokenize
from newspaper import Article
import nltk

# Web scraping
from playwright.sync_api import sync_playwright, Page, Browser

# Data processing
import pandas as pd
from itertools import combinations
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Entity:
    """Represents an extracted named entity."""
    name: str
    label: str
    sent_idx: int
    start: int
    end: int
    url: str

    def to_dict(self) -> dict:
        return {
            'name': self.name, 'label': self.label, 'sent_idx': self.sent_idx,
            'start': self.start, 'end': self.end, 'urls': self.url
        }


@dataclass
class Edge:
    """Represents a relationship edge between two entities."""
    source: str
    target: str
    edge_type: str

    def to_dict(self) -> dict:
        return {'source': self.source, 'target': self.target, 'type': self.edge_type}

    def __hash__(self):
        return hash(frozenset([self.source, self.target]))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return frozenset([self.source, self.target]) == frozenset([other.source, other.target])


# =============================================================================
# NLP Processor
# =============================================================================

class NLPProcessor:
    """Handles entity extraction and coreference resolution."""

    def __init__(self, model: str = 'en_core_web_lg'):
        self.nlp = spacy.load(model)
        self.nlp.add_pipe('coreferee')
        self.target_labels = {'PERSON', 'ORG'}

    def clean_entity_name(self, text: str) -> str:
        return text.replace('\n', ' ').replace("'s", "").strip()

    def extract_entities(self, sentence: str, sent_idx: int, url: str) -> List[Entity]:
        """Extract PERSON and ORG entities from a sentence."""
        doc = self.nlp(sentence)
        entities = []
        for ent in doc.ents:
            if ent.label_ in self.target_labels:
                name = self.clean_entity_name(ent.text)
                if name:
                    entities.append(Entity(name, ent.label_, sent_idx, ent.start, ent.end, url))
        return entities

    def get_coreference_chains(self, doc) -> List[List[int]]:
        """Extract coreference chains as lists of token indices."""
        chains = []
        if doc._.coref_chains:
            for chain in doc._.coref_chains:
                indices = []
                for mention in chain:
                    indices.extend(mention.token_indexes)
                chains.append(indices)
        return chains

    def get_sentence_for_token(self, doc, token_idx: int) -> int:
        """Get sentence index for a token."""
        for sent_idx, sent in enumerate(doc.sents):
            if sent.start <= token_idx < sent.end:
                return sent_idx
        return -1


# =============================================================================
# Web Scraping Functions (Playwright)
# =============================================================================

def navigate_to_news(page: Page) -> None:
    """Navigate to the News tab in Google search results."""
    try:
        news_tab = page.locator("a:has-text('News')").first
        news_tab.click(timeout=10000)
        page.wait_for_load_state('networkidle')
    except Exception:
        for link in page.locator('.hdtb-mitem a').all():
            href = link.get_attribute('href') or ''
            if 'news' in href.lower():
                link.click()
                page.wait_for_load_state('networkidle')
                return


def extract_urls(page: Page) -> List[str]:
    """Extract news article URLs from the current page."""
    urls = []
    for link in page.locator('.ftSUBd a').all():
        href = link.get_attribute('href')
        if href:
            urls.append(href)
    return list(set(urls))


def search_news(query: str, count: int, headless: bool = True) -> List[str]:
    """Search Google News and collect article URLs using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            page.goto('https://www.google.com')
            page.wait_for_selector('input[name="q"]', timeout=10000)
            page.fill('input[name="q"]', query)
            page.press('input[name="q"]', 'Enter')
            page.wait_for_load_state('networkidle')

            navigate_to_news(page)
            urls = extract_urls(page)

            while len(urls) < count:
                try:
                    next_btn = page.locator('#pnnext')
                    if next_btn.count() == 0:
                        break
                    next_btn.click()
                    page.wait_for_load_state('networkidle')
                    navigate_to_news(page)
                    urls.extend(extract_urls(page))
                    urls = list(set(urls))
                except Exception:
                    break

            return urls[:count]
        finally:
            browser.close()


def download_article(url: str) -> Optional[dict]:
    """Download and parse an article using newspaper4k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        return {'url': url, 'text': article.text, 'title': article.title}
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return None


# =============================================================================
# Graph Building Functions
# =============================================================================

def is_valid_pair(e1: dict, e2: dict) -> bool:
    """Check if entity pair should create an edge."""
    if e1['name'] == e2['name'] or not e1['name'] or not e2['name']:
        return False
    return not (e1['label'] == 'ORG' and e2['label'] == 'ORG')


def extract_edges_from_entities(entities: List[dict], coref_chains: List[dict]) -> Set[Edge]:
    """Extract edges from same-sentence co-occurrences and coreference chains."""
    edges = set()

    # Group entities by (url, sentence)
    by_sentence: Dict[Tuple[str, int], List[dict]] = {}
    for ent in entities:
        key = (ent['urls'], ent['sent_idx'])
        by_sentence.setdefault(key, []).append(ent)

    # Same-sentence edges
    for ents in by_sentence.values():
        if len(ents) >= 2:
            for e1, e2 in combinations(ents, 2):
                if is_valid_pair(e1, e2):
                    edges.add(Edge(e1['name'], e2['name'], f"{e1['label']}-{e2['label']}"))

    # Coreference-based edges
    for chain in coref_chains:
        chain_entities = []
        for sent_idx in chain['sentences']:
            key = (chain['url'], sent_idx)
            chain_entities.extend(by_sentence.get(key, []))

        if len(chain_entities) >= 2:
            for e1, e2 in combinations(chain_entities, 2):
                if is_valid_pair(e1, e2):
                    edges.add(Edge(e1['name'], e2['name'], f"{e1['label']}-{e2['label']}"))

    return edges


# =============================================================================
# Main Pipeline
# =============================================================================

def clip_search(query: str, count: int, headless: bool = True) -> pd.DataFrame:
    """
    Main pipeline: scrape articles, extract entities, build relationship graph.

    Args:
        query: Search query string
        count: Target number of articles
        headless: Run browser in headless mode

    Returns:
        DataFrame with columns: source, target, type
    """
    # Step 1: Scrape news URLs
    logger.info(f"Searching for: {query}")
    news_urls = search_news(query, count, headless)
    logger.info(f"Found {len(news_urls)} URLs")

    # Step 2: Download articles
    articles = [a for url in news_urls if (a := download_article(url))]
    logger.info(f"Downloaded {len(articles)} articles")

    # Step 3: Process with NLP
    processor = NLPProcessor()
    all_entities = []
    all_coref_chains = []

    for article in articles:
        if not article.get('text'):
            continue

        url = article['url']
        text = article['text']
        doc = processor.nlp(text)
        sentences = sent_tokenize(text)

        # Extract entities
        for sent_idx, sentence in enumerate(sentences):
            for ent in processor.extract_entities(sentence, sent_idx, url):
                all_entities.append(ent.to_dict())

        # Extract coreference chains
        chains = processor.get_coreference_chains(doc)
        for chain_idx, chain in enumerate(chains):
            chain_sents = set()
            for token_idx in chain:
                sent_idx = processor.get_sentence_for_token(doc, token_idx)
                if sent_idx >= 0:
                    chain_sents.add(sent_idx)
            if len(chain_sents) > 1:
                all_coref_chains.append({'chain_idx': chain_idx, 'sentences': list(chain_sents), 'url': url})

    # Step 4: Build graph
    edges = extract_edges_from_entities(all_entities, all_coref_chains)
    logger.info(f"Created {len(edges)} edges")

    return pd.DataFrame([e.to_dict() for e in edges]) if edges else pd.DataFrame(columns=['source', 'target', 'type'])

# =============================================================================
# Visualization
# =============================================================================

ENTITY_COLORS = {
    'PERSON': '#4CAF50', 'ORG': '#2196F3',
    'PERSON-ORG': '#FF9800', 'ORG-PERSON': '#FF9800', 'PERSON-PERSON': '#9C27B0'
}


def infer_node_types(edges_df: pd.DataFrame) -> Dict[str, str]:
    """Infer node types from edge types."""
    node_types = {}
    for _, row in edges_df.iterrows():
        if '-' in str(row.get('type', '')):
            t1, t2 = row['type'].split('-')
            node_types.setdefault(row['source'], t1)
            node_types.setdefault(row['target'], t2)
    return node_types


def create_visualization(edges_df: pd.DataFrame) -> Network:
    """Create a PyVis network visualization."""
    G = nx.from_pandas_edgelist(edges_df, 'source', 'target', edge_attr='type')
    node_types = infer_node_types(edges_df)

    net = Network(height='600px', width='100%', bgcolor='#222222', font_color='white',
                  notebook=False, cdn_resources='in_line')

    for node in G.nodes():
        ntype = node_types.get(node, 'PERSON')
        net.add_node(node, label=node, color=ENTITY_COLORS.get(ntype, '#FFFFFF'),
                     title=f"{node} ({ntype})")

    for s, t, data in G.edges(data=True):
        etype = data.get('type', '')
        net.add_edge(s, t, color=ENTITY_COLORS.get(etype, '#888888'))

    net.repulsion(node_distance=420, central_gravity=0.33, spring_length=110,
                  spring_strength=0.10, damping=0.95)
    return net


def save_and_display_graph(net: Network) -> str:
    """Save graph to HTML and return the file content."""
    output_path = '/tmp/pyvis_graph.html'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(output_path)
    with open(output_path, 'r', encoding='utf-8') as f:
        return f.read()


# =============================================================================
# Streamlit App
# =============================================================================

st.title('clip-search.ai')

with st.form("form"):
    query_val = st.text_input("Enter your search query here:")
    count_val = st.number_input("How many articles do you want to scrape?",
                                 min_value=10, max_value=200, step=10)
    submitted = st.form_submit_button("Submit")

    if submitted:
        with st.spinner('Searching and processing articles...'):
            links = clip_search(query_val, count_val)

        if links.empty:
            st.warning("No relationships found. Try a different query or more articles.")
        else:
            st.success(f"Found {len(links)} entity relationships!")
            net = create_visualization(links)
            html_content = save_and_display_graph(net)
            components.html(html_content, height=600, width=800)