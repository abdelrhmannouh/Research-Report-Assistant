import argparse
import sys
from pathlib import Path

from src.client import ReportClient, ReportError
from src.config import get_settings
from src.models import ReportResult


def main() -> int:
    parser = argparse.ArgumentParser(description="Research a topic and write a cited report.")
    parser.add_argument("topic", nargs="*", help="topic to research (prompted if omitted)")
    parser.add_argument("-o", "--out", type=Path, help="also save the report to this Markdown file")
    args = parser.parse_args()

    topic = " ".join(args.topic).strip() or input("Enter a search topic: ").strip()
    if len(topic) < 3:
        print("Please enter a topic (at least 3 characters).", file=sys.stderr)
        return 2

    client = ReportClient(get_settings().api_url)
    result = None
    try:
        for item in client.stream(topic):
            if isinstance(item, ReportResult):
                result = item
            elif item.status == "started":
                print(f"… {item.stage}", file=sys.stderr)
            else:
                extra = f" ({item.detail})" if item.detail else ""
                print(f"✓ {item.stage} {item.elapsed:.1f}s{extra}", file=sys.stderr)
    except ReportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    markdown = result.to_markdown()
    print(markdown)
    if args.out:
        args.out.write_text(markdown, encoding="utf-8")
        print(f"Saved to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
