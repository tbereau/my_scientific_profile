from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from my_scientific_profile.unpaywall.works import get_unpaywall_work_by_doi

__all__ = ["OpenAccessStatus", "OpenAccessPaperInfo", "get_open_access_paper_info"]


class OpenAccessStatus(Enum):
    GREEN = "green"
    BRONZE = "bronze"
    HYBRID = "hybrid"
    GOLD = "gold"


@dataclass(frozen=True)
class OpenAccessPaperInfo:
    is_open_access: bool
    open_access_status: Optional[OpenAccessStatus] = field(default=None)
    landing_page_url: Optional[str] = field(default=None)
    pdf_url: Optional[str] = field(default=None)


def get_open_access_paper_info(doi: str) -> OpenAccessPaperInfo:
    unpaywall_info = get_unpaywall_work_by_doi(doi)
    oa_status, landing_page_url, pdf_url = None, None, None
    is_oa = unpaywall_info.is_oa
    if is_oa:
        oa_status = OpenAccessStatus(unpaywall_info.oa_status)
        best_oa_location = unpaywall_info.best_oa_location
        if best_oa_location:
            landing_page_url = best_oa_location.url_for_landing_page or None
            pdf_url = best_oa_location.url_for_pdf or None
    return OpenAccessPaperInfo(is_oa, oa_status, landing_page_url, pdf_url)
