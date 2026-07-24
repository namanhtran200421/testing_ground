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
OUTPUT_CRAWL_AUDIT_PATH = PROCESSED_DATA_DIR / "crawled_pages.csv"
OUTPUT_PRODUCTION_FINAL_PATH = PROCESSED_DATA_DIR / "production_final.csv"
OUTPUT_TRANSLATION_PATH = PROCESSED_DATA_DIR / "production_500_sample.csv"
OUTPUT_TRANSLATION_CACHE_PATH = PROCESSED_DATA_DIR / "translation_cache.csv"
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
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/150.0.0.0 Safari/537.36"
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

# Notebook 02 crawler and semantic-selection configuration.
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MAX_CRAWL_DEPTH = 3
MAX_PAGES_PER_COMPANY = 12
MAX_CHILDREN_PER_PAGE = 2
MIN_LINK_SIMILARITY = 0.38
MIN_CONTENT_SIMILARITY = 0.42
MIN_SEMANTIC_MARGIN = 0.06
MIN_HEADING_SIMILARITY = 0.38
MAX_HEADING_CHARACTERS = 150
MAX_SECTION_ELEMENTS = 30
MAX_SECTION_CHARACTERS = 4_000
MIN_SECTION_CHARACTERS = 80
MIN_PAGE_TEXT_CHARACTERS = 300
MIN_PAGE_TEXT_WORDS = 40
MAX_PAGE_TEXT_CHARACTERS = 10_000
CONTENT_SCORING_CHARACTERS = 10_000

PRIMARY_VALUE_HEADING_PATTERNS = [
    r"\bour values?\b",
    r"\bcore values?\b",
    r"\bcompany values?\b",
    r"\bcorporate values?\b",
    r"\bshared values?\b",
    r"\borganisational values?\b",
    r"\borganizational values?\b",
    r"\bour principles?\b",
    r"\bcore principles?\b",
    r"\bguiding principles?\b",
    r"\bcompany principles?\b",
    r"\bour beliefs?\b",
    r"\bcompany beliefs?\b",
    r"\bwhat we believe\b",
    r"\bwhat we stand for\b",
    r"\bvalues? and behavio(?:u)?rs?\b",
    r"\bour commitments?\b",
    r"\bethical principles?\b",
    r"\bour culture\b",
    r"\bcompany culture\b",
    r"\bour philosophy\b",
    r"\bcompany philosophy\b",
    r"\bour ethos\b",
    r"\bcorporate ethos\b",
    r"\bour dna\b",
]

PRIMARY_VALUE_HEADING_THEMES = [
    "our values", "core values", "company values", "corporate values",
    "our principles", "guiding principles", "core principles", "our beliefs",
    "what we believe", "what we stand for", "values and behaviours",
    "values and behaviors", "our commitments", "ethical principles",
    "our culture", "company culture", "our philosophy", "our ethos", "our DNA",
    "how we behave", "how we work",
]
SUPPORTING_HEADING_THEMES = [
    "our mission", "company mission", "our vision", "company vision",
    "our purpose", "company purpose", "our identity",
]
SECTION_HEADING_THEMES = PRIMARY_VALUE_HEADING_THEMES + SUPPORTING_HEADING_THEMES

TARGET_LINK_THEMES = [
    "our core values", "company core values", "corporate values",
    "organisational values", "organizational values", "company principles",
    "guiding principles", "core principles", "our beliefs", "company beliefs",
    "what we believe", "our purpose", "company purpose", "our mission",
    "company mission", "our vision", "company vision",
    "mission vision and values", "purpose mission vision and values",
    "our culture", "company culture", "workplace culture",
    "organisational culture", "organizational culture", "shared values",
    "values and behaviours", "values and behaviors", "our commitments",
    "company commitments", "ethical principles", "business ethics",
    "code of values", "principles that guide us", "what guides our decisions",
    "how we work", "how we behave", "who we are and what we stand for",
    "what we stand for", "our identity and values", "our philosophy",
    "company philosophy", "our ethos", "corporate ethos", "our DNA",
    "company DNA", "our way", "the way we work", "our standards",
    "company standards", "our foundations", "our values and culture",
    "our mission and values", "our vision and values", "our purpose and values",
    "our principles and values",
]

TARGET_CONTENT_THEMES = [
    "The company explicitly explains its core values, guiding principles, beliefs, or standards that influence employee behaviour and business decisions.",
    "The page describes mission, vision, or purpose together with the organisation's values, principles, beliefs, or expected behaviours.",
    "The company presents named values such as integrity, respect, innovation, collaboration, accountability, trust, excellence, inclusion, or sustainability.",
    "The page explains the behaviours expected from employees and how the organisation's values guide everyday work.",
    "The company describes its organisational culture, shared values, workplace beliefs, and the principles that shape how people work together.",
    "The page contains a structured list of company values, each supported by an explanation, definition, example, or behavioural statement.",
    "The company explains what it stands for, what it believes in, and the principles used to guide choices and relationships with stakeholders.",
    "The organisation defines its ethical principles, commitments, or standards of conduct as part of its identity and culture.",
    "The page explains the company's philosophy, ethos, identity, or DNA in terms of values, beliefs, purpose, and expected behaviour.",
    "The company describes how its mission, purpose, vision, culture, and values connect to its long-term direction and decision-making.",
]

NEGATIVE_CONTENT_THEMES = [
    "A page advertising leadership training, management development, coaching, workshops, academies, courses, or professional education services.",
    "A page describing a commercial training programme, academy, consulting service, learning product, or customer offering.",
    "A page explaining how a service helps customers develop leadership, culture, vision, behaviours, purpose, or organisational values.",
    "The page mainly discusses corporate governance, board structure, executive oversight, committees, compliance, or shareholder responsibilities.",
    "The page mainly contains investor relations information, annual reports, financial performance, stock information, or corporate disclosures.",
    "The page mainly provides contact details, office locations, enquiry forms, phone numbers, email addresses, or customer support information.",
    "The page mainly lists jobs, vacancies, recruitment information, employee benefits, or career opportunities.",
    "The page mainly describes products, services, industries, capabilities, customer solutions, or commercial offerings.",
    "The page mainly contains news articles, press releases, media updates, events, announcements, or blog posts.",
]

SECTION_VERIFICATION_THEMES = [
    "The organisation explicitly states its own core values, beliefs, principles, mission, vision, purpose, or expected behaviours.",
    "This section describes what the company itself stands for and how its employees or leaders are expected to behave.",
    "This section presents the organisation's identity, culture, values, mission, vision, or guiding principles.",
]
SECTION_REJECTION_THEMES = [
    "This section describes company history, restructuring, reorganisation, business divisions, factories, milestones, anniversaries, or past events.",
    "This section describes governance structures, boards, committees, directors, reporting responsibilities, ESG governance, or oversight bodies.",
    "This section is specifically about a product specification, technical feature, equipment model, product catalogue, or service description.",
    "This section is specifically about a project, event, news story, programme, gallery, membership, or temporary initiative.",
    "This section contains legal conditions, contractual clauses, privacy terms, prices, monetary value, inventory value, or compliance declarations.",
    "This section mainly lists addresses, phone numbers, email details, office locations, staff members, executives, or organisational roles.",
    "This section mainly describes employment vacancies, job applications, career opportunities, or recruitment instructions.",
]

EXCLUDED_PATH_PATTERNS = [
    r"/contact(?:/|$)", r"/privacy(?:/|$)", r"/terms(?:/|$)",
    r"/terms-of-use(?:/|$)", r"/termos-de-uso(?:/|$)", r"/legal(?:/|$)",
    r"/login(?:/|$)", r"/signin(?:/|$)", r"/search(?:/|$)", r"/cart(?:/|$)",
    r"/checkout(?:/|$)", r"/author(?:/|$)", r"/tag(?:/|$)",
    r"/category(?:/|$)", r"/news(?:/|$)", r"/blog(?:/|$)",
    r"/press(?:/|$)", r"/media(?:/|$)", r"/jobs?(?:/|$)",
    r"/careers?(?:/|$)", r"/vacanc(?:y|ies)(?:/|$)",
    r"/recruitment(?:/|$)", r"/board-of-directors(?:/|$)",
    r"/[^/]*management-team(?:/|$)", r"/[^/]*leadership-team(?:/|$)",
    r"/[^/]*board-of-directors(?:/|$)",
    r"/[^/]*executive-committee(?:/|$)", r"/corporate-governance(?:/|$)",
    r"/investor-relations(?:/|$)", r"/awards?(?:/|$)",
    r"/milestones?(?:/|$)", r"/clients?(?:/|$)", r"/customers?(?:/|$)",
    r"/partners?(?:/|$)", r"/brands?(?:/|$)", r"/franchises?(?:/|$)",
    r"/groupcompanies(?:/|$)", r"/group-companies(?:/|$)",
    r"/team(?:/|$)", r"/our-team(?:/|$)", r"/people(?:/|$)",
    r"/certifications?(?:/|$)", r"/accreditations?(?:/|$)",
    r"/quality-assurance(?:/|$)", r"/quality(?:/|$)",
    r"/products?(?:/|$)", r"/services?(?:/|$)", r"/solutions?(?:/|$)",
    r"/industries?(?:/|$)", r"/case-studies?(?:/|$)",
    r"/resources?(?:/|$)", r"/events?(?:/|$)", r"/mental-health(?:/|$)",
    r"/governance(?:/|$)", r"/governanca(?:/|$)",
    r"/company-profile(?:/|$)", r"/noticias?(?:/|$)",
]
EXCLUDED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip", ".doc",
    ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}
ANCHOR_TEXT_NOISE = {
    "", "skip to content", "skip to main content", "click here", "read more",
    "learn more", "more", "menu", "close", "next", "previous", "back", "top",
}
EXCLUDED_SECTION_ANCESTORS = {
    "script", "style", "noscript", "svg", "button", "nav", "footer", "form",
    "aside", "header",
}

VALUE_SECTION_PATTERNS = [
    r"\bour values\b", r"\bcore values\b", r"\bcompany values\b",
    r"\bour principles\b", r"\bguiding principles\b", r"\bwhat we believe\b",
    r"\bwhat we stand for\b", r"\bmission.{0,40}vision.{0,40}values\b",
    r"\bpurpose.{0,40}values\b", r"\bvalues and behaviours\b",
    r"\bvalues and behaviors\b", r"\bour philosophy\b",
    r"\bcompany philosophy\b", r"\bour culture\b", r"\bcompany culture\b",
]
VALUE_WORD_PATTERNS = [
    r"\bintegrity\b", r"\brespect\b", r"\baccountability\b",
    r"\bexcellence\b", r"\bcollaboration\b", r"\binnovation\b", r"\btrust\b",
    r"\binclusion\b", r"\bsustainability\b", r"\bcommitment\b", r"\bcourage\b",
    r"\bsafety\b", r"\bcitizenship\b",
]
POSITIVE_VALUE_PATH_PATTERNS = [
    r"/values?(?:/|$)", r"/core-values?(?:/|$)", r"/our-values?(?:/|$)",
    r"/werte(?:/|$)", r"/nos-valeurs(?:/|$)", r"/valeurs(?:/|$)",
    r"/principles?(?:/|$)", r"/beliefs?(?:/|$)",
    r"/mission-and-values?(?:/|$)", r"/vision-and-values?(?:/|$)",
    r"/purpose-and-values?(?:/|$)", r"/mission-vision-values?(?:/|$)",
    r"/[^/]*vision-mission(?:/|$)", r"/[^/]*mission-vision(?:/|$)",
]

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "translategemma:4b"
MAX_CONCURRENT_TRANSLATIONS = 2
MAX_TRANSLATION_RETRIES = 3
TRANSLATION_TIMEOUT_SECONDS = 120

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
