#!/usr/bin/env python3
"""
Extract Wikipedia articles from XML dump and convert to plain text JSON.

This script parses a Wikipedia XML dump file and extracts articles,
converting WikiML markup to plain text.
"""

import xml.etree.ElementTree as ET
import re
import json
import html
import argparse
from pathlib import Path


def clean_wikitext(text):
    """
    Convert WikiML markup to plain text by removing templates, links,
    HTML tags, and other formatting.

    Args:
        text: Raw wikitext string

    Returns:
        Cleaned plain text string
    """
    if not text:
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove <ref> tags and their content
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/?>", "", text)

    # Remove other HTML tags but keep their content
    text = re.sub(r"<references\s*/>", "", text)
    text = re.sub(r"<[^>]+>", "", text)

    # Remove templates (nested curly braces)
    # This is complex due to nesting, so we iterate
    prev_text = None
    while prev_text != text:
        prev_text = text
        # Remove simple templates
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    # Clean up any remaining template artifacts
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.DOTALL)
    text = text.replace("{{", "").replace("}}", "")

    # Convert wiki links [[target|display]] to just display text
    # or [[target]] to target
    text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)

    # Remove external links [url text] -> text
    text = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\s\]]+\]", "", text)

    # Remove file/image links
    text = re.sub(r"\[\[File:.*?\]\]", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[Immagine:.*?\]\]", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[Image:.*?\]\]", "", text, flags=re.DOTALL)

    # Remove category tags
    text = re.sub(r"\[\[Categoria:.*?\]\]", "", text)
    text = re.sub(r"\[\[Category:.*?\]\]", "", text)

    # Remove headings markup but keep text
    text = re.sub(r"={2,}([^=]+)={2,}", r"\1", text)

    # Remove bold and italic markup
    text = re.sub(r"'{2,}", "", text)

    # Remove table markup
    text = re.sub(r"\{\|.*?\|\}", "", text, flags=re.DOTALL)

    # Remove bullets and numbering
    text = re.sub(r"^\*+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^:+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^;+\s*", "", text, flags=re.MULTILINE)

    # Clean up multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean up whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def extract_articles(xml_file, output_file):
    """
    Extract articles from Wikipedia XML dump and save as JSON.

    Args:
        xml_file: Path to the XML dump file
        output_file: Path to the output JSON file
    """
    print(f"Parsing XML file: {xml_file}")

    # Define namespace for MediaWiki XML
    ns = {"mw": "http://www.mediawiki.org/xml/export-0.11/"}

    articles = []

    # Use iterparse for memory efficiency with large files
    context = ET.iterparse(xml_file, events=("end",))

    count = 0
    for event, elem in context:
        if elem.tag == "{http://www.mediawiki.org/xml/export-0.11/}page":
            # Extract title
            title_elem = elem.find("mw:title", ns)
            if title_elem is None:
                elem.clear()
                continue

            title = title_elem.text

            # Extract namespace
            ns_elem = elem.find("mw:ns", ns)
            namespace = ns_elem.text if ns_elem is not None else "0"

            # Only process main namespace articles (ns=0)
            if namespace != "0":
                elem.clear()
                continue

            # Extract page ID
            id_elem = elem.find("mw:id", ns)
            page_id = id_elem.text if id_elem is not None else None

            # Extract text from revision
            revision = elem.find("mw:revision", ns)
            if revision is not None:
                text_elem = revision.find("mw:text", ns)
                if text_elem is not None and text_elem.text:
                    wikitext = text_elem.text
                    plain_text = clean_wikitext(wikitext)

                    if plain_text:  # Only add if there's actual content
                        articles.append({"id": page_id, "title": title, "text": plain_text})

                        count += 1
                        if count % 100 == 0:
                            print(f"Processed {count} articles...")

            # Clear element to free memory
            elem.clear()

    print(f"\nExtracted {len(articles)} articles")
    print(f"Writing to {output_file}")

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("Done!")


def main():
    parser = argparse.ArgumentParser(description="Extract Wikipedia articles from XML dump to JSON")
    parser.add_argument(
        "input_file",
        nargs="?",
        default="itwiki-latest-pages-articles-multistream1.xml",
        help="Input XML file (default: itwiki-latest-pages-articles-multistream1.xml)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="dict/wikipedia_articles.json",
        help="Output JSON file (default: dict/wikipedia_articles.json)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        return 1

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    extract_articles(str(input_path), str(output_path))
    return 0


if __name__ == "__main__":
    exit(main())
