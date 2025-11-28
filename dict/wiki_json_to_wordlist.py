#!/usr/bin/env python3
"""
Generate a word frequency list from Wikipedia articles JSON.

This script reads extracted Wikipedia articles and creates a list of the most
frequent words, useful for language learning and dictionary creation.
"""

import json
import re
import argparse
from pathlib import Path
from collections import Counter


def tokenize_text(text):
    """
    Extract words from text, converting to lowercase and removing punctuation.

    Args:
        text: Input text string

    Returns:
        List of words
    """
    # Convert to lowercase
    text = text.lower()

    # Extract words (Italian letters, including accented characters)
    words = re.findall(r"[a-zàáâäèéêëìíîïòóôöùúûüçñ']+", text)

    return words


def generate_wordlist(input_file, output_file, top_n=1000):
    """
    Generate a word frequency list from Wikipedia articles.

    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output text file
        top_n: Number of most frequent words to include
    """
    print(f"Reading articles from {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Processing {len(articles)} articles...")

    # Count word frequencies
    word_counter = Counter()

    for article in articles:
        text = article.get("text", "")
        words = tokenize_text(text)
        word_counter.update(words)

    print(f"Found {len(word_counter)} unique words")

    # Get top N words
    top_words = word_counter.most_common(top_n)

    print(f"Writing top {len(top_words)} words to {output_file}")

    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        for word, count in top_words:
            f.write(f"{word}\n")

    print("Done!")
    print("\nMost common words:")
    for i, (word, count) in enumerate(top_words[:10], 1):
        print(f"  {i}. {word}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate word frequency list from Wikipedia articles"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="dict/wikipedia_articles.json",
        help="Input JSON file (default: dict/wikipedia_articles.json)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="dict/words.txt",
        help="Output text file (default: dict/words.txt)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=1000,
        help="Number of most frequent words to include (default: 1000)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        return 1

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_wordlist(str(input_path), str(output_path), args.top)
    return 0


if __name__ == "__main__":
    exit(main())
