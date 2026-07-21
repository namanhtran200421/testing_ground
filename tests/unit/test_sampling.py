from __future__ import annotations

import pandas as pd

from country_values_distance.sampling import sample_candidates


def test_sample_candidates_is_deterministic_with_same_seed() -> None:
    frame = pd.DataFrame(
        [
            {
                "country": "france",
                "size_bucket": "small",
                "High_Level_Sector": "Retail",
                "name": "Company A",
            },
            {
                "country": "france",
                "size_bucket": "small",
                "High_Level_Sector": "Retail",
                "name": "Company B",
            },
            {
                "country": "france",
                "size_bucket": "small",
                "High_Level_Sector": "Retail",
                "name": "Company C",
            },
            {
                "country": "france",
                "size_bucket": "medium",
                "High_Level_Sector": "Retail",
                "name": "Company D",
            },
        ]
    )

    first_run = sample_candidates(frame)
    second_run = sample_candidates(frame)

    pd.testing.assert_frame_equal(first_run, second_run)
