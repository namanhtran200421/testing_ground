import pandas as pd

from country_values_distance.config import (
    MAX_COMPANIES_PER_COUNTRY,
    MAX_COMPANIES_PER_SECTOR_PER_SIZE,
    RANDOM_SEED,
    REQUIRED_SAMPLING_COLUMNS,
    SIZE_TARGETS,
)

def sample_country_candidates(
    country_group: pd.DataFrame,
) -> pd.DataFrame:
    sampled_size_groups: list[pd.DataFrame] = []

    for size_bucket, target_count in SIZE_TARGETS.items():
        size_group = country_group[
            country_group["size_bucket"] == size_bucket
        ].copy()

        if size_group.empty:
            continue

        sector_samples: list[pd.DataFrame] = []

        for _, sector_group in size_group.groupby(
            "High_Level_Sector",
            sort=True,
        ):
            sampled_sector = sector_group.sample(
                n=min(
                    MAX_COMPANIES_PER_SECTOR_PER_SIZE,
                    len(sector_group),
                ),
                random_state=RANDOM_SEED,
            )

            sector_samples.append(sampled_sector)

        if not sector_samples:
            continue

        sampled_size_group = pd.concat(
            sector_samples,
            ignore_index=False,
        )

        if len(sampled_size_group) > target_count:
            sampled_size_group = sampled_size_group.sample(
                n=target_count,
                random_state=RANDOM_SEED,
            )

        if len(sampled_size_group) < target_count:
            remaining_needed = target_count - len(sampled_size_group)

            remaining_pool = size_group.drop(
                index=sampled_size_group.index,
                errors="ignore",
            )

            if not remaining_pool.empty:
                top_up = remaining_pool.sample(
                    n=min(remaining_needed, len(remaining_pool)),
                    random_state=RANDOM_SEED,
                )

                sampled_size_group = pd.concat(
                    [sampled_size_group, top_up],
                    ignore_index=False,
                )

        sampled_size_groups.append(sampled_size_group)

    if not sampled_size_groups:
        return country_group.sample(
            n=min(
                MAX_COMPANIES_PER_COUNTRY,
                len(country_group),
            ),
            random_state=RANDOM_SEED,
        )

    sampled_country = pd.concat(
        sampled_size_groups,
        ignore_index=False,
    )

    if len(sampled_country) > MAX_COMPANIES_PER_COUNTRY:
        sampled_country = sampled_country.sample(
            n=MAX_COMPANIES_PER_COUNTRY,
            random_state=RANDOM_SEED,
        )

    return sampled_country


def sample_candidates(
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    missing_columns = REQUIRED_SAMPLING_COLUMNS.difference(
        candidates.columns
    )

    if missing_columns:
        raise ValueError(
            f"Missing required sampling columns: {sorted(missing_columns)}"
        )

    if candidates.empty:
        return candidates.copy()

    sampled_countries: list[pd.DataFrame] = []

    for _, country_group in candidates.groupby(
        "country",
        sort=True,
    ):
        sampled_country = sample_country_candidates(
            country_group=country_group,
        )

        sampled_countries.append(sampled_country)

    sampled_candidates = pd.concat(
        sampled_countries,
        ignore_index=True,
    )

    return (
        sampled_candidates
        .sort_values(
            [
                "country",
                "size_bucket",
                "High_Level_Sector",
                "name",
            ]
        )
        .reset_index(drop=True)
    )