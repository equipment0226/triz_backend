"""Public, fixed-path files used by Google Search Console and crawlers."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)
PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"


@router.api_route("/googledb97084bf62cb561.html", methods=["GET", "HEAD"])
def google_site_verification():
    return FileResponse(
        PUBLIC_DIR / "googledb97084bf62cb561.html", media_type="text/html"
    )


@router.api_route("/robots.txt", methods=["GET", "HEAD"])
def robots():
    return FileResponse(PUBLIC_DIR / "robots.txt", media_type="text/plain")


@router.api_route("/sitemap.xml", methods=["GET", "HEAD"])
def sitemap():
    return FileResponse(PUBLIC_DIR / "sitemap.xml", media_type="application/xml")
