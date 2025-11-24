import requests
import pdfplumber

GOOD_KEYWORDS = [
    "order", "contract", "awarded", "bagged", "win", "l1", "l-1", "agreement",
    "results", "profit", "revenue", "q1", "q2", "q3", "q4", "fy",
    "dividend", "bonus", "split", "buyback", "rights issue",
    "preferential issue",
    "investment", "acquisition", "epc", "mdo", "project", "mine",
    "bauxite", "crore"
]


def is_good_news(headline: str) -> bool:
    h = (headline or "").lower()
    return any(k in h for k in GOOD_KEYWORDS)


def fetch_bse_announcements(from_date: str, to_date: str, page: int = 1):
    """
    Call BSE 'w' endpoint and return raw JSON.
    from_date / to_date format: YYYYMMDD
    """
    url = "https://www.bseindia.com/corporates/w"

    params = {
        "pageno": page,
        "strCat": "",
        "strPrevDate": from_date,
        "strToDate": to_date,
        "strType": "ANN",
        "scd": "",
        "sname": "",
        "subCategory": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.bseindia.com/corporates/ann.html",
        "Origin": "https://www.bseindia.com",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def parse_announcements(raw_data):
    """
    Transform BSE JSON rows into a clean, filtered list.
    """
    results = []

    if not raw_data:
        return results

    for row in raw_data:
        headline = row.get("HEADLINE") or row.get("HEADING") or ""
        pdf_raw = row.get("ATTACHMENTNAME") or ""

        pdf_url = None
        if ".pdf" in str(pdf_raw):
            pdf_url = "https://www.bseindia.com" + pdf_raw.replace("..", "")

        item = {
            "company": row.get("CO_NAME") or row.get("COMPANYNAME"),
            "scripcode": row.get("SCRIP_CD"),
            "headline": headline,
            "date": row.get("NEWS_DT") or row.get("NEWSSUB"),
            "pdf": pdf_url,
            "is_good": is_good_news(headline),
        }

        results.append(item)

    return results


def download_pdf(url: str, filename: str = "/tmp/news.pdf") -> str | None:
    """
    Download PDF to /tmp (Render's writable dir) and return path.
    """
    if not url:
        return None

    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    if resp.status_code == 200:
        with open(filename, "wb") as f:
            f.write(resp.content)
        return filename

    return None


def extract_pdf_text(filepath: str) -> str:
    """
    Extract plain text from a PDF file.
    """
    if not filepath:
        return ""

    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        # Don't crash the service if PDF is weird
        return ""

    return text.strip()
