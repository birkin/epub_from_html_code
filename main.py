"""
converts an html file into an epub ebook, using headings as chapters
"""

import argparse
import os
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub

## load constants
BOOK_AUTHOR: str = os.environ['BOOK_AUTHOR']
BOOK_IDENTIFIER: str = os.environ['BOOK_IDENTIFIER']
BOOK_LANGUAGE: str = os.environ['BOOK_LANGUAGE']
BOOK_TITLE: str = os.environ['BOOK_TITLE']


def make_chapter(title: str, html_content: list[str], idx: int) -> epub.EpubHtml:
    """
    Creates a chapter from the given title and HTML content.
    """
    chptr: epub.EpubHtml = epub.EpubHtml(title=title, file_name=f'chap_{idx}.xhtml', lang='en')
    chptr.content: str = str(html_content)
    return chptr


def main(html_path: Path) -> None:
    """
    Converts an HTML file to an EPUB ebook, using headings as chapter breaks.

    The function:
    - Parses the HTML content using BeautifulSoup
    - Creates a new EPUB book with metadata
    - Splits content into chapters based on heading elements
    - Generates an EPUB file in the same directory as the input file
    """

    ## load and parse the HTML
    soup: BeautifulSoup
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')

    book: epub.EpubBook = epub.EpubBook()
    book.set_identifier(BOOK_IDENTIFIER)
    book.set_title(BOOK_TITLE)
    book.set_language(BOOK_LANGUAGE)
    book.add_author(BOOK_AUTHOR)

    ## find main content (adapt selector as needed)
    article: BeautifulSoup | None = soup.find('article')
    if not article:
        article = soup.body

    chapters: list[epub.EpubHtml] = []
    chapter_count: int = 1

    current_chapter: list[str] = []
    current_title: str = 'Introduction'

    for el in article.children:
        ## heading = start new chapter
        if el.name and el.name in ['h1', 'h2']:
            if current_chapter:
                chap: epub.EpubHtml = make_chapter(current_title, current_chapter, chapter_count)
                chapters.append(chap)
                book.add_item(chap)
                chapter_count += 1
                current_chapter = []
            current_title = el.get_text()
        if getattr(el, 'name', None):
            current_chapter.append(str(el))

    ## add last chapter
    if current_chapter:
        chap = make_chapter(current_title, current_chapter, chapter_count)
        chapters.append(chap)
        book.add_item(chap)

    ## define Table of Contents
    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    ## add default CSS
    style: str = 'BODY { font-family: Gentium, Georgia, serif; }'
    nav_css: epub.EpubItem = epub.EpubItem(uid='style_nav', file_name='style/nav.css', media_type='text/css', content=style)
    book.add_item(nav_css)

    ## write to file
    output_path: Path = html_path.with_suffix('.epub')
    epub.write_epub(str(output_path), book, {})
    print(f'EPUB created: {output_path}')

    ## end def main()


def validate_html_file(path: Path) -> Path:
    """
    Validates that the path exists and has an .html extension.
    """
    if not path.exists():
        raise FileNotFoundError(f'File not found: {path}')
    if path.suffix.lower() != '.html':
        raise ValueError(f'File must have an .html extension, got: {path.suffix}')
    return path


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Convert an HTML file to an EPUB ebook, using headings as chapters')
    parser.add_argument(
        '--html_path',
        type=lambda p: validate_html_file(Path(p)),
        required=True,
        help='Path to the input HTML file (must end with .html)',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args: argparse.Namespace = parse_args()
    html_path: Path = args.html_path
    main(html_path)
