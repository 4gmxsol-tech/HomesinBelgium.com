#!/usr/bin/env python3
"""Validate local HTML links and fragment targets across the static site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag.lower() == "a" and attrs.get("href") is not None:
            self.links.append(attrs["href"])

def resolve_target(source, raw_href):
    parts = urlsplit(raw_href.strip())
    if parts.scheme or parts.netloc:
        return None, parts.fragment
    path = unquote(parts.path)
    if not path:
        target = source
    elif path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = source.parent / path
    target = target.resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return None, parts.fragment
    if target.is_dir() or raw_href.strip().endswith("/"):
        target = target / "index.html"
    if not target.exists() and not target.suffix:
        html_candidate = target.with_suffix(".html")
        if html_candidate.exists():
            target = html_candidate
    return target, unquote(parts.fragment)

def main():
    pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    errors = []
    checked = 0
    for source in pages:
        parser = PageParser()
        try:
            parser.feed(source.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError) as exc:
            errors.append(f"{source.relative_to(ROOT)}: cannot parse HTML: {exc}")
            continue
        for href in parser.links:
            href = href.strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            target, fragment = resolve_target(source, href)
            if target is None:
                continue
            checked += 1
            if not target.is_file():
                errors.append(f"{source.relative_to(ROOT)} -> {href}: target does not exist")
                continue
            if fragment:
                target_parser = PageParser()
                try:
                    target_parser.feed(target.read_text(encoding="utf-8"))
                except (UnicodeDecodeError, OSError) as exc:
                    errors.append(f"{source.relative_to(ROOT)} -> {href}: cannot read target: {exc}")
                    continue
                if fragment not in target_parser.ids:
                    errors.append(f"{source.relative_to(ROOT)} -> {href}: fragment #{fragment} not found")
    print(f"Checked {checked} local links across {len(pages)} HTML pages.")
    if errors:
        print("\n".join(errors))
        print(f"FAILED: {len(errors)} broken local link(s).")
        return 1
    print("PASS: all local links and fragment targets resolve.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
