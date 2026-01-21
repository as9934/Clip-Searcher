"""
NLTK Download Utilities

Downloads required NLTK data packages for sentence tokenization.
"""
import nltk


def download_nltk_data():
    """Download required NLTK data packages."""
    packages = ['punkt', 'punkt_tab']
    for package in packages:
        nltk.download(package, quiet=True)


if __name__ == '__main__':
    download_nltk_data()
