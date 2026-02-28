NEWS_SOURCES = [
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/where/iran/",
        "base_url": "https://www.aljazeera.com",
    },
    {
        "name": "Reuters",
        "url": "https://www.reuters.com/world/middle-east/",
        "base_url": "https://www.reuters.com",
    },
    {
        "name": "BBC News",
        "url": "https://www.bbc.com/news/topics/cwlw3xz047jt",
        "base_url": "https://www.bbc.com",
    },
    {
        "name": "AP News",
        "url": "https://apnews.com/hub/iran",
        "base_url": "https://apnews.com",
    },
    {
        "name": "CNN",
        "url": "https://edition.cnn.com/middleeast",
        "base_url": "https://edition.cnn.com",
    },
]

SCRAPE_INTERVAL_SECONDS = 3600  # 1 hour

CONFLICT_KEYWORDS = [
    "bomb", "bombing", "strike", "airstrike", "air strike",
    "attack", "killed", "missile", "explosion", "casualties",
    "shelling", "raid", "drone", "artillery", "blast",
    "war", "combat", "offensive", "military operation",
]

IRAN_KEYWORDS = [
    "iran", "tehran", "isfahan", "tabriz", "shiraz", "mashhad",
    "ahvaz", "kermanshah", "qom", "karaj", "bushehr", "bandar abbas",
    "persian gulf", "strait of hormuz", "khuzestan", "kurdistan",
    "iranian", "irgc", "revolutionary guard",
]
