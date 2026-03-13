from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fin_insight_graph_agent.ingestion.connectors.http_transport import HttpTransport


@dataclass(slots=True)
class SecEdgarClient:
    user_agent: str
    base_url: str = "https://data.sec.gov"
    transport: HttpTransport | Any = HttpTransport()

    def fetch_submissions(self, cik: str) -> dict[str, Any]:
        padded_cik = self._pad_cik(cik)
        return self.transport.get_json(
            f"{self.base_url}/submissions/CIK{padded_cik}.json",
            headers=self._headers(),
        )

    def fetch_company_facts(self, cik: str) -> dict[str, Any]:
        padded_cik = self._pad_cik(cik)
        return self.transport.get_json(
            f"{self.base_url}/api/xbrl/companyfacts/CIK{padded_cik}.json",
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        }

    @staticmethod
    def _pad_cik(cik: str) -> str:
        return cik.zfill(10)