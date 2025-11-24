from fastapi import FastAPI, Query
from typing import Optional

from bse_scraper import (
    fetch_bse_announcements,
    parse_announcements,
    download_pdf,
    extract_pdf_text,
)

app = FastAPI(title="BSE Scraper Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fetch-bse")
def fetch_bse(
    from_date: str = Query(..., description="Start date in YYYYMMDD (BSE format)"),
    to_date: str = Query(..., description="End date in YYYYMMDD (BSE format)"),
    page: int = Query(1, ge=1, description="Page number"),
    only_good: bool = Query(True, description="If true, return only 'good news'")
):
    """
    Fetch announcements from BSE and return parsed JSON.

    Example:
    /fetch-bse?from_date=20251120&to_date=20251124&only_good=true
    """
    raw = fetch_bse_announcements(from_date=from_date, to_date=to_date, page=page)
    parsed = parse_announcements(raw)

    if only_good:
        parsed = [r for r in parsed if r["is_good"]]

    return {
        "count": len(parsed),
        "items": parsed,
    }


@app.get("/fetch-bse-and-pdf")
def fetch_bse_and_pdf(
    from_date: str = Query(..., description="Start date in YYYYMMDD"),
    to_date: str = Query(..., description="End date in YYYYMMDD"),
    page: int = Query(1, ge=1),
    index: int = Query(0, ge=0, description="Which item index to download PDF for"),
):
    """
    Fetch announcements, pick one by index, download its PDF and return text.
    This is mainly for testing; your pipeline later will call AI with this text.
    """
    raw = fetch_bse_announcements(from_date=from_date, to_date=to_date, page=page)
    parsed = parse_announcements(raw)

    if not parsed:
        return {"error": "No announcements found"}

    if index >= len(parsed):
        return {"error": f"Index {index} out of range, total {len(parsed)}"}

    item = parsed[index]

    if not item["pdf"]:
        return {"error": "No PDF attached for this item", "item": item}

    pdf_path = download_pdf(item["pdf"], "/tmp/bse_item.pdf")
    text = extract_pdf_text(pdf_path)

    return {
        "item": item,
        "text_preview": text[:2000],  # first ~2000 chars
        "text_length": len(text),
    }
