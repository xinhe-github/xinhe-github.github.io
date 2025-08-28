import os
import re
import sys
from datetime import datetime

try:
    import bibtexparser
except Exception as e:
    print("Missing dependency: bibtexparser. Install with: sudo apt install python3-bibtexparser -y")
    sys.exit(1)


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "publication"


def html_escape(text: str) -> str:
    # Escape characters for safe YAML/HTML
    return (
        text.replace("\\", "\\\\")
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
        .replace("{", "")
        .replace("}", "")
    )


def format_authors(authors_field: str) -> str:
    # BibTeX authors separated by ' and '
    parts = [a.strip() for a in authors_field.split(" and ") if a.strip()]
    return ", ".join(parts)


def map_category(entry_type: str) -> str:
    t = (entry_type or "").lower()
    if t in ("article",):
        return "manuscripts"
    if t in ("inproceedings", "proceedings", "conference", "incollection"):
        return "conferences"
    if t in ("book", "inbook"):
        return "books"
    return "manuscripts"


def extract_date(entry: dict) -> str:
    # Prefer year + month/day if present; default to Jan 1 of year
    year = entry.get("year", "").strip()
    month = entry.get("month", "").strip()
    day = entry.get("day", "").strip()
    if not year:
        # fallback to current year to keep Jekyll happy
        year = str(datetime.utcnow().year)
    # Normalize month to number if textual
    month_map = {
        "jan": "01", "january": "01",
        "feb": "02", "february": "02",
        "mar": "03", "march": "03",
        "apr": "04", "april": "04",
        "may": "05",
        "jun": "06", "june": "06",
        "jul": "07", "july": "07",
        "aug": "08", "august": "08",
        "sep": "09", "sept": "09", "september": "09",
        "oct": "10", "october": "10",
        "nov": "11", "november": "11",
        "dec": "12", "december": "12",
    }
    m = month.lower()
    if m in month_map:
        month_num = month_map[m]
    else:
        month_num = ("%02d" % int(month)) if month.isdigit() else "01"
    d = ("%02d" % int(day)) if day.isdigit() else "01"
    return f"{year}-{month_num}-{d}"


def build_venue(entry: dict) -> str:
    return entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""


def build_urls(entry: dict) -> tuple[str, str]:
    doi = entry.get("doi", "").strip()
    url = entry.get("url", "").strip()
    paper_url = (f"https://doi.org/{doi}" if doi and not doi.lower().startswith("http") else doi) or url
    slides_url = ""
    return paper_url, slides_url


def build_citation(entry: dict) -> str:
    authors = format_authors(entry.get("author", "").strip())
    title = entry.get("title", "").strip().strip("{}")
    venue = build_venue(entry)
    year = entry.get("year", "").strip()
    bits = []
    if authors:
        bits.append(authors)
    if title:
        bits.append(f'"{title}."')
    if venue:
        bits.append(venue)
    if year:
        bits.append(year)
    return " ".join(bits)


def write_publication(entry: dict, out_dir: str) -> None:
    title = entry.get("title", "").strip() or "Untitled"
    title = html_escape(title)
    pub_date = extract_date(entry)
    url_slug = slugify(title)
    html_filename = f"{pub_date}-{url_slug}"

    excerpt = ""
    venue = html_escape(build_venue(entry))
    paper_url, slides_url = build_urls(entry)
    citation = html_escape(build_citation(entry))
    category = map_category(entry.get("ENTRYTYPE", ""))

    md = []
    md.append("---")
    md.append(f'title: "{title}"')
    md.append("collection: publications")
    md.append(f"permalink: /publication/{html_filename}")
    if excerpt:
        md.append(f"excerpt: '{html_escape(excerpt)}'")
    md.append(f"date: {pub_date}")
    if venue:
        md.append(f"venue: '{venue}'")
    if paper_url:
        md.append(f"paperurl: '{paper_url}'")
    if citation:
        md.append(f"citation: '{citation}'")
    if category:
        md.append(f"category: {category}")
    md.append("---")
    md.append("")
    if paper_url:
        md.append(f"<a href='{paper_url}'>Download paper here</a>")
        md.append("")
    if excerpt:
        md.append(html_escape(excerpt))
        md.append("")
    if citation:
        md.append(f"Recommended citation: {citation}")

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{html_filename}.md"), "w") as f:
        f.write("\n".join(md))


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bibtex_to_publications.py path/to/export.bib")
        sys.exit(1)
    bib_path = sys.argv[1]
    if not os.path.isfile(bib_path):
        print(f"File not found: {bib_path}")
        sys.exit(1)

    with open(bib_path) as bibtex_file:
        bib_db = bibtexparser.load(bibtex_file)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "_publications")
    count = 0
    for entry in bib_db.entries:
        try:
            write_publication(entry, out_dir)
            count += 1
        except Exception as e:
            print(f"Failed to write entry {entry.get('ID', '(no id)')}: {e}")
    print(f"Wrote {count} publication files to {out_dir}")


if __name__ == "__main__":
    main()
