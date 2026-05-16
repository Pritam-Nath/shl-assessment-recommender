import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = "https://www.shl.com"
LIST_URL = ROOT + "/solutions/products/product-catalog?start={start}&type=1"
OUT = Path(__file__).resolve().parent.parent / "data" / "shl_catalog.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SHLAssignmentBot/1.0)"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_list_items(page: str) -> list[dict]:
    marker = "Individual Test Solutions"
    start = page.find(marker)
    if start == -1:
        return []
    table = page[start : page.find("</table>", start)]
    rows = re.findall(r"<tr[^>]*data-entity-id=.*?</tr>", table, flags=re.S)
    items = []
    for row in rows:
        link_match = re.search(r'<a href="([^"]+)">(.*?)</a>', row, flags=re.S)
        if not link_match:
            continue
        href, name_html = link_match.groups()
        keys = re.findall(r'product-catalogue__key"[^>]*>([A-Z])</span>', row)
        cells = re.findall(r'<td class="custom__table-heading__general">(.*?)</td>', row, flags=re.S)
        remote = len(cells) > 0 and "-yes" in cells[0]
        adaptive = len(cells) > 1 and "-yes" in cells[1]
        url = urllib.parse.urljoin(ROOT, href)
        items.append(
            {
                "name": clean(name_html),
                "url": url,
                "test_type": "".join(keys),
                "remote_testing": remote,
                "adaptive_irt": adaptive,
            }
        )
    return items


def extract_after_heading(page: str, heading: str) -> str:
    idx = page.find(f"<h4>{heading}</h4>")
    if idx == -1:
        return ""
    block = page[idx : page.find("</div>", idx)]
    paragraph = re.search(r"<p>(.*?)</p>", block, flags=re.S)
    if paragraph:
        return clean(paragraph.group(1))
    return clean(block.replace(f"<h4>{heading}</h4>", ""))


def enrich(item: dict) -> dict:
    page = fetch(item["url"])
    h1 = re.search(r"<h1>(.*?)</h1>", page, flags=re.S)
    if h1:
        item["name"] = clean(h1.group(1))
    item["description"] = extract_after_heading(page, "Description")
    item["job_levels"] = extract_after_heading(page, "Job levels")
    item["languages"] = extract_after_heading(page, "Languages")
    duration = re.search(r"Approximate Completion Time in minutes\s*=\s*([0-9]+)", page)
    item["duration"] = duration.group(1) if duration else ""
    detail_keys = re.findall(r"Test Type:\s*</h4>.*?(?:product-catalogue__key[^>]*>([A-Z])</span>)+", page, flags=re.S)
    if detail_keys:
        item["test_type"] = "".join(detail_keys)
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", action="store_true", help="Fetch each assessment detail page for richer metadata.")
    args = parser.parse_args()

    seen = {}
    for start in range(0, 900, 12):
        page = fetch(LIST_URL.format(start=start))
        items = extract_list_items(page)
        if not items:
            break
        for item in items:
            seen[item["url"]] = item
        print(f"Fetched list page start={start}: {len(items)} items")
        if len(items) < 12:
            break
        time.sleep(0.2)

    enriched = list(seen.values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(enriched)} list items to {OUT}")

    if args.details:
        enriched = []
        for idx, item in enumerate(seen.values(), start=1):
            try:
                enriched.append(enrich(item))
                print(f"{idx}/{len(seen)} {item['name']}")
            except Exception as exc:
                print(f"Warning: detail fetch failed for {item['url']}: {exc}")
                enriched.append(item)
            time.sleep(0.1)

        OUT.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(enriched)} enriched catalog items to {OUT}")


if __name__ == "__main__":
    main()
