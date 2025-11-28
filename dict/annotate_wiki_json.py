#!/usr/bin/env python3
"""
Generate Italian-English dictionary entries using Claude API.

This script processes Wikipedia articles and uses Claude to extract
grammatical information and translations for each word.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from anthropic import Anthropic


def read_api_key():
    """Read Claude API key from ~/.claude-api-key"""
    api_key_path = Path.home() / ".claude-api-key"
    if not api_key_path.exists():
        print(f"Error: API key file not found at {api_key_path}", file=sys.stderr)
        sys.exit(1)
    return api_key_path.read_text().strip()


def read_prompt():
    """Read the prompt template from prompt.txt"""
    prompt_path = Path(__file__).parent / "prompt.txt"
    if not prompt_path.exists():
        print(f"Error: Prompt file not found at {prompt_path}", file=sys.stderr)
        sys.exit(1)
    return prompt_path.read_text()


def truncate_text(text, max_words):
    """Truncate text to first N words"""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def process_article(client, prompt, article, max_words, model):
    """
    Process a single article with Claude API.

    Args:
        client: Anthropic client
        prompt: System prompt text
        article: Article dict with 'title' and 'text'
        max_words: Maximum words to send from article
        model: Model ID to use

    Returns:
        Tuple of (rows, input_tokens, output_tokens)
    """
    article_text = truncate_text(article["text"], max_words)

    # Create the message with streaming (required for long requests)
    with client.messages.stream(
        model=model,
        max_tokens=64000,
        system=prompt,
        messages=[{"role": "user", "content": article_text}],
    ) as stream:
        # Accumulate the response
        response_text = stream.get_final_text()
        message = stream.get_final_message()

    # Extract token usage
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens

    # Parse CSV lines
    rows = []
    for line_num, line in enumerate(response_text.strip().split("\n"), 1):
        line = line.strip()
        if not line:
            continue

        # Parse CSV line
        try:
            # Simple CSV parsing - split by comma but respect that there are 8 fields
            parts = line.split(",")
            if len(parts) != 8:
                print(
                    f"Warning: Skipping malformed line {line_num} "
                    f"(expected 8 fields, got {len(parts)}): {line}",
                    file=sys.stderr,
                )
                continue
            rows.append(parts)
        except Exception as e:
            print(
                f"Warning: Skipping invalid line {line_num}: {line} ({e})",
                file=sys.stderr,
            )
            continue

    return rows, input_tokens, output_tokens


def calculate_cost(model, input_tokens, output_tokens):
    """
    Calculate the cost of API usage based on model and token counts.

    Args:
        model: Model ID
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in dollars
    """
    # Pricing per million tokens
    pricing = {
        "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    }

    if model not in pricing:
        return None

    input_cost = (input_tokens / 1_000_000) * pricing[model]["input"]
    output_cost = (output_tokens / 1_000_000) * pricing[model]["output"]

    return input_cost + output_cost


def main():
    parser = argparse.ArgumentParser(
        description="Generate Italian-English dictionary using Claude API"
    )
    parser.add_argument(
        "-n",
        "--num-articles",
        type=int,
        default=1,
        help="Number of articles to process (default: 1)",
    )
    parser.add_argument(
        "-w",
        "--max-words",
        type=int,
        default=1000,
        help="Maximum words per article (default: 1000)",
    )
    parser.add_argument(
        "--sonnet",
        action="store_true",
        help="Use Claude Sonnet 4.5 instead of Haiku 4.5",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of articles to skip (default: 0)",
    )
    parser.add_argument(
        "--input",
        default=str(Path(__file__).parent / "wikipedia_articles.json"),
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "dict.csv"),
    )

    args = parser.parse_args()

    # Select model based on flag
    model = "claude-sonnet-4-5-20250929" if args.sonnet else "claude-haiku-4-5-20251001"

    # Read API key and prompt
    api_key = read_api_key()
    prompt = read_prompt()

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    # Load articles
    print(f"Loading articles from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Skip articles and take the next N
    start_idx = args.skip
    end_idx = args.skip + args.num_articles
    articles_to_process = articles[start_idx:end_idx]
    print(
        f"Processing {len(articles_to_process)} article(s) (skipping first {args.skip}) with {model}..."
    )

    # Prepare output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    total_input_tokens = 0
    total_output_tokens = 0

    # Open CSV file
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Process each article
        for idx, article in enumerate(articles_to_process, 1):
            title = article.get("title", "Unknown")
            print(f"[{idx}/{len(articles_to_process)}] Processing: {title}")

            rows, input_tokens, output_tokens = process_article(
                client, prompt, article, args.max_words, model
            )
            # Write rows immediately
            writer.writerows(rows)
            f.flush()  # Ensure data is written to disk
            total_rows += len(rows)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            print(f"  → Extracted {len(rows)} words")

    print(f"\nWrote {total_rows} entries to {args.output}")
    print("Done!")

    # Calculate and display cost
    print("\nToken usage:")
    print(f"  Input tokens:  {total_input_tokens:,}")
    print(f"  Output tokens: {total_output_tokens:,}")

    cost = calculate_cost(model, total_input_tokens, total_output_tokens)
    if cost is not None:
        print(f"\nEstimated cost: ${cost:.4f}")


if __name__ == "__main__":
    main()
