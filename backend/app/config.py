NEWS_SOURCES = [
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/where/iran/",
        "base_url": "https://www.aljazeera.com",
        "feed_url": "https://www.aljazeera.com/xml/rss/all.xml",
    },
    {
        "name": "Reuters",
        "url": "https://www.reuters.com/world/middle-east/",
        "base_url": "https://www.reuters.com",
        "feed_url": None,
    },
    {
        "name": "BBC News",
        "url": "https://www.bbc.com/news/topics/cwlw3xz047jt",
        "base_url": "https://www.bbc.com",
        "feed_url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
    },
    {
        "name": "AP News",
        "url": "https://apnews.com/hub/iran",
        "base_url": "https://apnews.com",
        "feed_url": None,
    },
    {
        "name": "CNN",
        "url": "https://edition.cnn.com/middleeast",
        "base_url": "https://edition.cnn.com",
        "feed_url": "http://rss.cnn.com/rss/edition_meast.rss",
    },
    {
        "name": "VG",
        "url": "https://www.vg.no/nyheter/utenriks/",
        "base_url": "https://www.vg.no",
        "feed_url": None,
    },
]

# Google News search RSS feeds — most reliable aggregation source
GOOGLE_NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=Iran+strike+bombing+missile+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Iran+airstrike+killed+casualties+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Iran+war+attack+military+strike+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Tehran+Isfahan+missile+strike+when:7d&hl=en-US&gl=US&ceid=US:en",
]

SCRAPE_INTERVAL_SECONDS = 3600  # 1 hour

CONFLICT_KEYWORDS = [
    "bomb", "bombing", "strike", "airstrike", "air strike",
    "missile", "explosion", "shelling", "artillery", "blast",
    "drone strike", "raid", "killed", "casualties",
    "offensive", "military operation",
    "attack", "attacked", "bombardment", "target", "targeted",
    "destroy", "destroyed", "combat", "battle",
    "cruise missile", "ballistic missile", "intercepted",
    "drone", "warplane", "fighter jet", "sortie",
    "warfare", "strikes", "bombings", "rockets", "rocket",
    "weapons", "munitions", "warhead", "detonation",
    "killing", "deaths", "dead", "fatalities",
]

IRAN_KEYWORDS = [
    "iran", "iranian", "tehran", "isfahan", "tabriz", "shiraz", "mashhad",
    "ahvaz", "kermanshah", "qom", "karaj", "bushehr", "bandar abbas",
    "persian gulf", "strait of hormuz", "khuzestan", "kurdistan",
    "irgc", "revolutionary guard",
    "parchin", "natanz", "fordow", "arak",
    "abadan", "dezful", "khorramshahr", "hamadan",
    "rasht", "kerman", "yazd", "ardabil", "zahedan",
    "gorgan", "sari", "semnan", "birjand", "ilam",
    "sanandaj", "khorramabad",
    "persian", "islamic republic",
    "khamenei", "rouhani", "raisi",
    "quds force", "basij",
    "esfahan", "khoramshahr", "bandar-abbas",
    "chabahar", "bam", "bojnurd", "zanjan", "urmia",
]
