import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Brand, Platform, Mention, ReputationScore, CrisisEvent, Influencer

BRANDS = [
    ("TechNova", "Technology", "🚀"), ("GreenLeaf Foods", "Food & Beverage", "🍃"),
    ("UrbanStyle", "Fashion", "👗"), ("FinanceHub", "Financial Services", "💰"),
    ("HealthFirst", "Healthcare", "🏥"), ("CloudMatrix", "Cloud Computing", "☁️"),
    ("EcoMotors", "Automotive", "🚗"), ("MediaPulse", "Media", "📺"),
    ("FitLife Pro", "Fitness", "💪"), ("TravelEase", "Travel", "✈️"),
]

PLATFORMS = [("Twitter/X", "🐦"), ("Reddit", "🔴"), ("LinkedIn", "💼"), ("Instagram", "📸"),
             ("YouTube", "▶️"), ("TikTok", "🎵"), ("News Sites", "📰"), ("Review Sites", "⭐")]

TOPICS = ["product quality", "customer service", "pricing", "innovation", "sustainability",
          "leadership", "data privacy", "workplace culture", "marketing", "competitor comparison"]

POS_TEMPLATES = [
    "Amazing experience with {brand}! Their {topic} is top-notch.",
    "Just switched to {brand} and couldn't be happier. Great {topic}!",
    "{brand} really understands {topic}. Highly recommended!",
    "5 stars for {brand}'s approach to {topic}. Industry leader!",
]
NEG_TEMPLATES = [
    "Disappointed with {brand}'s {topic}. Need improvement.",
    "{brand} really dropped the ball on {topic}. Looking for alternatives.",
    "Can't believe {brand}'s {topic} issues. Not acceptable in 2025.",
    "Switching away from {brand}. Their {topic} is terrible.",
]
NEU_TEMPLATES = [
    "{brand} announced changes to their {topic} strategy.",
    "Comparing {brand}'s {topic} with competitors. Mixed results.",
    "{brand}'s {topic} is decent but nothing special.",
]

CRISIS_TEMPLATES = [
    ("{brand} Data Breach Report", "critical", "Reports of customer data exposure affecting thousands of users."),
    ("{brand} PR Controversy", "high", "Viral social media post sparks debate about {brand}'s practices."),
    ("{brand} Service Outage", "medium", "Extended downtime affecting customer operations for 6+ hours."),
    ("{brand} Exec Resignation", "medium", "Senior leadership change raises questions about direction."),
    ("{brand} Pricing Backlash", "high", "Customer backlash over sudden 40% price increase."),
    ("{brand} Product Recall", "critical", "Safety concerns trigger product recall affecting 10K units."),
]

INFLUENCER_NAMES = ["TechReviewPro", "DigitalSarah", "The_Real_Analyst", "BizInsiderMike",
                     "StartupJenny", "ConsumerWatch", "IndustryExpert99", "TrendSpotter",
                     "MarketMaven", "BrandCritic"]

async def seed_data(session: AsyncSession):
    random.seed(42)
    brands = []
    for name, industry, emoji in BRANDS:
        b = Brand(name=name, industry=industry, logo_emoji=emoji)
        session.add(b); brands.append(b)
    await session.flush()

    platforms = []
    for name, icon in PLATFORMS:
        p = Platform(name=name, icon=icon)
        session.add(p); platforms.append(p)
    await session.flush()

    # Generate mentions (2000+)
    base_date = datetime(2025, 4, 1)
    for _ in range(2500):
        brand = random.choice(brands)
        platform = random.choice(platforms)
        topic = random.choice(TOPICS)
        sentiment_roll = random.random()
        if sentiment_roll < 0.45:
            sentiment = "positive"; score = random.uniform(0.3, 1.0)
            content = random.choice(POS_TEMPLATES).format(brand=brand.name, topic=topic)
        elif sentiment_roll < 0.75:
            sentiment = "neutral"; score = random.uniform(-0.2, 0.2)
            content = random.choice(NEU_TEMPLATES).format(brand=brand.name, topic=topic)
        else:
            sentiment = "negative"; score = random.uniform(-1.0, -0.3)
            content = random.choice(NEG_TEMPLATES).format(brand=brand.name, topic=topic)

        m = Mention(brand_id=brand.id, platform_id=platform.id, content=content,
                    sentiment=sentiment, sentiment_score=round(score, 3),
                    reach=random.randint(100, 500000), engagement=random.randint(5, 10000),
                    date=base_date - timedelta(days=random.randint(0, 365)),
                    topic=topic)
        session.add(m)
    await session.flush()

    # Reputation scores (12 months per brand)
    for brand in brands:
        base_score = random.uniform(55, 85)
        for m_idx in range(12):
            month_date = base_date - timedelta(days=30 * (11 - m_idx))
            drift = random.uniform(-3, 4)
            base_score = max(20, min(95, base_score + drift))
            pos = random.uniform(35, 60); neg = random.uniform(10, 30); neu = 100 - pos - neg
            rs = ReputationScore(
                brand_id=brand.id, month=month_date.strftime("%Y-%m"),
                overall_score=round(base_score, 1), positive_pct=round(pos, 1),
                negative_pct=round(neg, 1), neutral_pct=round(neu, 1),
                total_mentions=random.randint(50, 500),
                total_reach=random.randint(50000, 5000000),
                avg_engagement=round(random.uniform(50, 2000), 1))
            session.add(rs)

    # Crisis events
    for _ in range(15):
        brand = random.choice(brands)
        tmpl = random.choice(CRISIS_TEMPLATES)
        ce = CrisisEvent(
            brand_id=brand.id, title=tmpl[0].format(brand=brand.name),
            severity=tmpl[1], date=base_date - timedelta(days=random.randint(0, 180)),
            description=tmpl[2].format(brand=brand.name),
            resolution_status=random.choice(["resolved", "monitoring", "escalated", "in_progress"]),
            sentiment_impact=round(random.uniform(-15, -2), 1))
        session.add(ce)

    # Influencers
    for brand in brands:
        for _ in range(random.randint(2, 5)):
            inf = Influencer(
                name=random.choice(INFLUENCER_NAMES) + str(random.randint(1, 99)),
                platform=random.choice(["Twitter/X", "YouTube", "Instagram", "TikTok"]),
                followers=random.randint(5000, 2000000),
                sentiment_toward_brand=random.choice(["positive", "negative", "neutral"]),
                influence_score=round(random.uniform(3, 10), 1),
                brand_id=brand.id)
            session.add(inf)

    await session.commit()
    print(f"Seeded: {len(brands)} brands, {len(platforms)} platforms, 2500 mentions, crisis events, influencers")
