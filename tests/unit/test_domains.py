from __future__ import annotations

import pandas as pd

from country_values_distance.domains import qualify_domains


def test_qualify_domains_classifies_keep_review_and_remove() -> None:
    frame = pd.DataFrame(
        [
            {
                "name": "Acme Corporation",
                "country": "france",
                "domain": "acme.fr",
            },
            {
                "name": "Another Company",
                "country": "france",
                "domain": "shared.example.com",
            },
            {
                "name": "Shared Company",
                "country": "france",
                "domain": "shared.example.com",
            },
            {
                "name": "Unrelated Company",
                "country": "france",
                "domain": "example.org",
            },
        ]
    )

    result = qualify_domains(frame)

    statuses = set(result.domain_checked["qualification_status"])
    assert statuses == {"keep", "review", "remove"}
    assert set(result.automatic_candidates["domain"]) == {"acme.fr"}
    assert result.review_candidates["domain"].eq("shared.example.com").any()
