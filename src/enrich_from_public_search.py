from __future__ import annotations

import csv
import argparse
import re
import time
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW_INPUT = ROOT / "data" / "raw" / "linkedin_profile_links_100.csv"
NOTES_OUTPUT = ROOT / "data" / "enrichment" / "linkedin_profile_notes.csv"


class DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_result = False
        self.current_text: list[str] = []
        self.results: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "") or ""
        if tag in {"a", "div"} and any(token in class_name for token in ["result__a", "result__snippet"]):
            self.in_result = True
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.in_result:
            cleaned = " ".join(data.split())
            if cleaned:
                self.current_text.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if self.in_result and tag in {"a", "div"}:
            text = " ".join(self.current_text).strip()
            if text:
                self.results.append(text)
            self.in_result = False
            self.current_text = []


def html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return " ".join(unescape(text).split())


def parse_bing_results(html: str) -> list[str]:
    results: list[str] = []
    for block in re.findall(r'(?is)<li class="b_algo".*?</li>', html):
        text = html_to_text(block)
        if text:
            results.append(text)
    if results:
        return results[:8]

    fallback_blocks = re.findall(r'(?is)<h2.*?</h2>.*?(?:<p.*?</p>)?', html)
    return [html_to_text(block) for block in fallback_blocks[:8] if html_to_text(block)]


def search_bing(query: str, timeout: int) -> str:
    search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
    request = Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GrowthPrototype/1.0)"},
    )
    with urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="ignore")
    return "\n".join(parse_bing_results(html))


def search_duckduckgo(query: str, timeout: int) -> str:
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    request = Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GrowthPrototype/1.0)"},
    )
    with urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = DuckDuckGoHTMLParser()
    parser.feed(html)
    return "\n".join(parser.results[:8])


def canonical_linkedin_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "in":
        return f"https://www.linkedin.com/in/{path_parts[1]}/"
    return url.strip()


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "in":
        return path_parts[1]
    return ""


def name_from_slug(slug: str) -> str:
    decoded = unquote(slug)
    parts = []
    for part in decoded.split("-"):
        part = re.sub(r"\d+$", "", part).strip()
        if part and not any(char.isdigit() for char in part):
            parts.append(part)
    return " ".join(parts).title()


def read_urls() -> list[str]:
    with RAW_INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [canonical_linkedin_url(row["linkedin_url"]) for row in reader if row.get("linkedin_url")]


def search_public_web(query: str, timeout: int) -> str:
    try:
        bing_text = search_bing(query, timeout=timeout)
        if bing_text.strip():
            return bing_text
    except Exception as bing_error:
        duck_text = search_duckduckgo(query, timeout=timeout)
        if duck_text.strip():
            return duck_text
        raise bing_error

    return search_duckduckgo(query, timeout=timeout)


def build_query(linkedin_url: str) -> str:
    slug = slug_from_url(linkedin_url)
    name = name_from_slug(slug)
    if slug and name:
        return f'"linkedin.com/in/{slug}" "{name}"'
    if slug:
        return f'"linkedin.com/in/{slug}"'
    return f'"{linkedin_url}"'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build enrichment notes from public search snippets.")
    parser.add_argument("--limit", type=int, default=0, help="Only process first N leads. 0 means all leads.")
    parser.add_argument("--sleep", type=float, default=1.5, help="Delay between search requests.")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    urls = read_urls()
    if args.limit:
        urls = urls[: args.limit]
    NOTES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for index, linkedin_url in enumerate(urls, start=1):
        query = build_query(linkedin_url)
        print(f"{index}/{len(urls)} searching: {query}", flush=True)
        try:
            profile_text = search_public_web(query, timeout=args.timeout)
        except Exception as exc:
            profile_text = f"PUBLIC_SEARCH_ERROR: {exc}"

        rows.append({"linkedin_url": linkedin_url, "profile_text": profile_text})
        print(f"{index}/{len(urls)} saved: {linkedin_url}", flush=True)
        time.sleep(args.sleep)

    with NOTES_OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["linkedin_url", "profile_text"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote public search enrichment notes to {NOTES_OUTPUT}", flush=True)
    print("Next: run python src/build_leads.py", flush=True)


if __name__ == "__main__":
    main()
