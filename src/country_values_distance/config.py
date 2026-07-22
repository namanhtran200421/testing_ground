from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_COMPANY_PATH = RAW_DATA_DIR / "dataset_country_test.csv"

OUTPUT_CLEANED_TARGET_COUNTRIES_PATH = (
    PROCESSED_DATA_DIR / "company_cleaned_target_countries.csv"
)
OUTPUT_DOMAIN_CHECKED_PATH = (
    PROCESSED_DATA_DIR / "company_domain_checked.csv"
)
OUTPUT_DUPLICATE_DOMAIN_REVIEW_PATH = (
    PROCESSED_DATA_DIR / "company_duplicate_domain_review.csv"
)
OUTPUT_REACHABLE_PATH = (
    PROCESSED_DATA_DIR / "company_reachable_websites.csv"
)
OUTPUT_UNREACHABLE_PATH = (
    PROCESSED_DATA_DIR / "company_unreachable_websites_reserve.csv"
)
OUTPUT_GOVERNMENT_SUMMARY_PATH = (
    PROCESSED_DATA_DIR / "government_ratio_summary.csv"
)
OUTPUT_SEED_SAMPLE_PATH = (
    PROCESSED_DATA_DIR / "company_seed_sample.csv"
)
OUTPUT_SCRAPE_READY_PATH = (
    PROCESSED_DATA_DIR / "company_scrape_ready.csv"
)

OUTPUT_AVAILABILITY_CHECK = (
    PROCESSED_DATA_DIR / "company_availability_check.csv"
)

OUTPUT_ROBOTS_VALIDATED_PATH = (
    PROCESSED_DATA_DIR / "company_robots_validated.csv"
)
OUTPUT_HOMEPAGE_FETCH_PATH = (
    PROCESSED_DATA_DIR / "company_homepage_fetch.csv"
)
OUTPUT_INTERNAL_LINKS_PATH = (
    PROCESSED_DATA_DIR / "company_internal_links.csv"
)
OUTPUT_INTERNAL_LINK_GROUPS_PATH = (
    PROCESSED_DATA_DIR / "company_internal_link_groups.csv"
)
OUTPUT_RUN_MANIFEST_PATH = (
    PROCESSED_DATA_DIR / "company_run_manifest.json"
)

HOMEPAGE_HTML_CACHE_DIR = PROCESSED_DATA_DIR / "homepage_html"


TARGET_COUNTRIES = [
    "australia",
    "germany",
    "south africa",
    "brazil",
    "turkey",
    "france",
    "saudi arabia",
    "china",
    "japan",
    "sri lanka",
]

COUNTRY_DOMAIN_SUFFIXES = {
    "australia": {"au"},
    "germany": {"de"},
    "south africa": {"za"},
    "brazil": {"br"},
    "turkey": {"tr"},
    "france": {"fr"},
    "saudi arabia": {"sa"},
    "china": {"cn"},
    "japan": {"jp"},
    "sri lanka": {"lk"},
}

LEGAL_COMPANY_WORDS = {
    "pty",
    "ltd",
    "limited",
    "corp",
    "corporation",
    "inc",
    "company",
    "co",
    "group",
    "holdings",
    "plc",
    "llc",
    "gmbh",
    "ag",
    "sa",
    "sarl",
    "bv",
    "nv",
}

BAD_DOMAIN_PATTERNS = [
    "instagram.com",
    "facebook.com",
    "facebook.com.br",
    "fb.me",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "linktr.ee",
    "lnk.bio",
    "campsite.bio",
    "instabio.cc",
    "bio.link",
    "wa.me",
    "weibo.com",
    "qq.com",
    "weebly.com",
    "wixsite.com",
    "wordpress.com",
    "blogspot.com",
    "business.site",
    "negocio.site",
    "sites.google.com",
    "g.page",
    "business.google.com",
    "medium.com",
    "github.com",
    "github.io",
    "behance.net",
    "vimeo.com",
    "soundcloud.com",
    "spotify.com",
    "anchor.fm",
    "ausha.co",
    "meetup.com",
    "calendly.com",
    "forms.gle",
    "docs.google.com",
    "drive.google.com",
    "mailchi.mp",
    "etsy.com",
    "mercadolibre",
    "1688.com",
    "wikipedia.org",
]

BAD_FILE_EXTENSIONS = [
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
]

SIZE_CATEGORY_MAP = {
    "1-10": "too_small",
    "11-50": "small",
    "51-200": "small",
    "201-500": "small",
    "501-1000": "medium",
    "1001-5000": "large",
    "5001-10000": "enterprise",
    "10001+": "enterprise",
}

REQUIRED_SAMPLING_COLUMNS = {
    "country",
    "size_bucket",
    "High_Level_Sector",
}

SIZE_TARGETS = {
    "small": 25,
    "medium": 25,
    "large": 25,
    "enterprise": 25,
}

MAX_FINAL_ROWS = 600
MAX_PER_COUNTRY = MAX_FINAL_ROWS // len(TARGET_COUNTRIES)
MAX_COMPANIES_PER_COUNTRY = 100
MAX_COMPANIES_PER_SECTOR_PER_SIZE = 5
MAX_PER_SECTOR_PER_COUNTRY = 5

GOVERNMENT_SECTOR = "Government, Public Sector & Civic"
MAX_GOVERNMENT_RATIO = 0.10
MAX_GOVERNMENT_PER_COUNTRY = int(MAX_PER_COUNTRY * MAX_GOVERNMENT_RATIO)

REQUEST_TIMEOUT_SECONDS = 15
MAX_CONCURRENT_REQUESTS = 10

USER_AGENT = (
    "Mozilla/5.0 (compatible; CompanyValuesResearchBot/1.0; "
    "+https://example.com/research)"
)

HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
}

DOMAIN_KEEP_MIN_SCORE = 80
DOMAIN_REVIEW_MIN_SCORE = 50

COUNTRY_WEBSITE_PRIORITY = {
    'country_match': 2,
    'global_or_unknown': 1,
    'country_missmatch': 0,
}

RANDOM_SEED = 42
DEFAULT_CHUNKSIZE = 100_000

SECTOR_TO_INDUSTRY = {
    "Agriculture, Food & Beverage": "dairy; farming; food & beverages; food production; wine and spirits",
    "Arts, Media & Entertainment": "writing and editing; animation; broadcast media; design; entertainment; fine art; media production; motion pictures and film; newspapers; online media; photography; printing; publishing; performing arts; music; computer games; museums and institutions; graphic design",
    "Automotive, Aerospace & Transportation Equipment": "automotive; aviation & aerospace; defense & space; shipbuilding",
    "Business Services & Administration": "capital markets; business supplies and equipment; executive office; facilities services; management consulting; outsourcing/offshoring; program development; staffing and recruiting",
    "Construction, Real Estate & Built Environment": "architecture & planning; building materials; civil engineering; commercial real estate; construction; real estate",
    "Consumer Goods & Retail": "apparel & fashion; consumer electronics; consumer goods; consumer services; cosmetics; furniture; luxury goods & jewelry; retail; sporting goods; supermarkets; textiles; wholesale",
    "Education & Research": "e-learning; education management; higher education; libraries; primary/secondary education; professional training & coaching; research",
    "Energy, Environment & Utilities": "environmental services; oil & energy; renewables & environment; utilities",
    "Financial Services & Insurance": "accounting; banking; financial services; insurance; investment banking; investment management; venture capital & private equity",
    "Government, Public Sector & Civic": "public policy; railroad manufacture; recreational facilities and service; government administration; government relations; international affairs; legislative office; military; political organization; think tanks; public relations and communications",
    "Healthcare & Life Sciences": "veterinary; alternative medicine; biotechnology; health, wellness and fitness; hospital & health care; medical devices; medical practice; mental health care; pharmaceuticals",
    "Hospitality, Travel & Leisure": "airlines/aviation; gambling & casinos; hospitality; leisure, travel & tourism; restaurants; sports",
    "Industrial Manufacturing & Materials": "chemicals; electrical/electronic manufacturing; glass, ceramics & concrete; industrial automation; machinery; mechanical or industrial engineering; mining & metals; packaging and containers; paper & forest products; plastics; semiconductors",
    "Information Technology & Internet": "computer & network security; computer hardware; computer networking; computer software; information services; information technology and services; internet; telecommunications; wireless; nanotechnology",
    "Legal & Justice": "judiciary; law enforcement; law practice; legal services; public safety; security and investigations",
    "Logistics, Transportation & Trade": "import and export; international trade and development; logistics and supply chain; maritime; package/freight delivery; transportation/trucking/railroad; warehousing",
    "Marketing, Communications & Events": "market research; events services; marketing and advertising; translation and localization",
    "Nonprofit, Social Services & Religion": "fund-raising; civic & social organization; individual & family services; non-profit organization management; religious institutions",
}

# Active workers plus queued websites can never exceed this value.
MAX_HTTP_OPERATIONS = 10
HTTP_WORKER_COUNT = 5
HTTP_QUEUE_CAPACITY = MAX_HTTP_OPERATIONS - HTTP_WORKER_COUNT

REQUEST_TIMEOUT_SECONDS = 15

HTTP_MAX_RETRIES = 2
HTTP_RETRY_BACKOFF_SECONDS = 0.25

TRANSIENT_HTTP_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}
MIN_CLEAN_CHARACTERS = 120
MIN_LETTERS = 80
MIN_LETTER_RATIO = 0.30
MAX_TEXT_CHARACTERS = 12_000
MAX_REPLACEMENT_RATIO = 0.002

RETRYABLE_FAILURE_REASONS = {
    "timeout",
    "connection_error",
}

CHECKPOINT_EVERY = 25
INDUSTRY_TO_SECTOR = {
    industry.strip().lower(): sector
    for sector, industries in SECTOR_TO_INDUSTRY.items()
    for industry in industries.split(";")
}

def map_industry_size(industry:str): 
    industry_clean = industry.strip().lower()
    return INDUSTRY_TO_SECTOR.get(industry_clean, 'Other')