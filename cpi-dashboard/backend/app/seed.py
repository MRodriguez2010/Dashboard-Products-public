"""Generate realistic demo data for the CPI Dashboard."""
import json
import random
from datetime import datetime, timedelta
from app.models import Category, Competitor, Product, PricePoint, PriceAlert, MarketEvent


DEMO_CATEGORIES = [
    {"name": "Project Management", "description": "Tools for team collaboration and project tracking"},
    {"name": "CRM Software", "description": "Customer relationship management platforms"},
    {"name": "Cloud Hosting", "description": "Infrastructure and cloud computing services"},
    {"name": "Email Marketing", "description": "Email automation and campaign management"},
    {"name": "Analytics & BI", "description": "Business intelligence and data analytics tools"},
]

DEMO_COMPETITORS = {
    "Project Management": [
        {"name": "Asana", "website": "asana.com", "tier": "mid-range", "market_share": 12,
         "products": [
            {"name": "Asana Starter", "price": 10.99, "type": "per-user/mo", "features": ["task management", "timeline", "boards"]},
            {"name": "Asana Advanced", "price": 24.99, "type": "per-user/mo", "features": ["portfolios", "goals", "custom fields", "forms"]},
            {"name": "Asana Enterprise", "price": 49.99, "type": "per-user/mo", "features": ["SAML", "data export", "admin controls"]},
         ]},
        {"name": "Monday.com", "website": "monday.com", "tier": "mid-range", "market_share": 15,
         "products": [
            {"name": "Monday Basic", "price": 9.00, "type": "per-user/mo", "features": ["boards", "docs", "200+ templates"]},
            {"name": "Monday Standard", "price": 12.00, "type": "per-user/mo", "features": ["timeline", "calendar", "guest access"]},
            {"name": "Monday Pro", "price": 19.00, "type": "per-user/mo", "features": ["automations", "integrations", "time tracking"]},
         ]},
        {"name": "Jira", "website": "atlassian.com", "tier": "enterprise", "market_share": 22,
         "products": [
            {"name": "Jira Free", "price": 0.00, "type": "per-user/mo", "features": ["scrum", "kanban", "10 users"]},
            {"name": "Jira Standard", "price": 8.15, "type": "per-user/mo", "features": ["advanced permissions", "audit logs"]},
            {"name": "Jira Premium", "price": 16.00, "type": "per-user/mo", "features": ["advanced roadmaps", "sandbox", "IP allowlisting"]},
         ]},
        {"name": "ClickUp", "website": "clickup.com", "tier": "budget", "market_share": 8,
         "products": [
            {"name": "ClickUp Unlimited", "price": 7.00, "type": "per-user/mo", "features": ["unlimited storage", "integrations", "dashboards"]},
            {"name": "ClickUp Business", "price": 12.00, "type": "per-user/mo", "features": ["automations", "timelines", "mind maps"]},
            {"name": "ClickUp Enterprise", "price": 19.00, "type": "per-user/mo", "features": ["SSO", "custom roles", "API"]},
         ]},
        {"name": "Basecamp", "website": "basecamp.com", "tier": "mid-range", "market_share": 5,
         "products": [
            {"name": "Basecamp Standard", "price": 15.00, "type": "per-user/mo", "features": ["projects", "messages", "to-dos"]},
            {"name": "Basecamp Pro Unlimited", "price": 299.00, "type": "monthly", "features": ["unlimited users", "admin tools", "priority support"]},
         ]},
        {"name": "Notion", "website": "notion.so", "tier": "budget", "market_share": 10,
         "products": [
            {"name": "Notion Plus", "price": 10.00, "type": "per-user/mo", "features": ["unlimited blocks", "file uploads", "version history"]},
            {"name": "Notion Business", "price": 18.00, "type": "per-user/mo", "features": ["SAML SSO", "bulk PDF export", "advanced permissions"]},
         ]},
    ],
    "CRM Software": [
        {"name": "Salesforce", "website": "salesforce.com", "tier": "enterprise", "market_share": 33,
         "products": [
            {"name": "SF Essentials", "price": 25.00, "type": "per-user/mo", "features": ["account management", "email integration"]},
            {"name": "SF Professional", "price": 80.00, "type": "per-user/mo", "features": ["forecasting", "lead scoring"]},
            {"name": "SF Enterprise", "price": 165.00, "type": "per-user/mo", "features": ["workflow automation", "API access"]},
         ]},
        {"name": "HubSpot", "website": "hubspot.com", "tier": "mid-range", "market_share": 18,
         "products": [
            {"name": "HubSpot Starter", "price": 20.00, "type": "per-user/mo", "features": ["contact management", "deal pipeline"]},
            {"name": "HubSpot Professional", "price": 100.00, "type": "per-user/mo", "features": ["automation", "sequences", "forecasting"]},
            {"name": "HubSpot Enterprise", "price": 150.00, "type": "per-user/mo", "features": ["predictive lead scoring", "custom objects"]},
         ]},
        {"name": "Pipedrive", "website": "pipedrive.com", "tier": "budget", "market_share": 8,
         "products": [
            {"name": "Pipedrive Essential", "price": 14.90, "type": "per-user/mo", "features": ["pipeline management", "custom fields"]},
            {"name": "Pipedrive Advanced", "price": 27.90, "type": "per-user/mo", "features": ["automations", "email sync"]},
            {"name": "Pipedrive Professional", "price": 49.90, "type": "per-user/mo", "features": ["revenue projections", "custom reports"]},
         ]},
        {"name": "Zoho CRM", "website": "zoho.com", "tier": "budget", "market_share": 12,
         "products": [
            {"name": "Zoho Standard", "price": 14.00, "type": "per-user/mo", "features": ["scoring rules", "workflows"]},
            {"name": "Zoho Professional", "price": 23.00, "type": "per-user/mo", "features": ["blueprints", "inventory management"]},
            {"name": "Zoho Enterprise", "price": 40.00, "type": "per-user/mo", "features": ["AI assistant", "multi-user portals"]},
         ]},
        {"name": "Freshsales", "website": "freshworks.com", "tier": "mid-range", "market_share": 6,
         "products": [
            {"name": "Freshsales Growth", "price": 15.00, "type": "per-user/mo", "features": ["contact lifecycle", "built-in chat"]},
            {"name": "Freshsales Pro", "price": 39.00, "type": "per-user/mo", "features": ["AI scoring", "workflows", "territory management"]},
            {"name": "Freshsales Enterprise", "price": 69.00, "type": "per-user/mo", "features": ["custom modules", "audit logs", "dedicated manager"]},
         ]},
    ],
    "Cloud Hosting": [
        {"name": "AWS", "website": "aws.amazon.com", "tier": "enterprise", "market_share": 32,
         "products": [
            {"name": "EC2 t3.micro", "price": 7.59, "type": "monthly", "features": ["1 vCPU", "1 GB RAM", "burst"]},
            {"name": "EC2 t3.medium", "price": 30.37, "type": "monthly", "features": ["2 vCPU", "4 GB RAM"]},
            {"name": "EC2 m5.large", "price": 70.08, "type": "monthly", "features": ["2 vCPU", "8 GB RAM", "balanced"]},
         ]},
        {"name": "Google Cloud", "website": "cloud.google.com", "tier": "enterprise", "market_share": 11,
         "products": [
            {"name": "GCP e2-micro", "price": 6.11, "type": "monthly", "features": ["0.25 vCPU", "1 GB RAM"]},
            {"name": "GCP e2-medium", "price": 24.46, "type": "monthly", "features": ["1 vCPU", "4 GB RAM"]},
            {"name": "GCP n1-standard-2", "price": 48.54, "type": "monthly", "features": ["2 vCPU", "7.5 GB RAM"]},
         ]},
        {"name": "Azure", "website": "azure.microsoft.com", "tier": "enterprise", "market_share": 23,
         "products": [
            {"name": "Azure B1s", "price": 7.59, "type": "monthly", "features": ["1 vCPU", "1 GB RAM"]},
            {"name": "Azure B2s", "price": 30.37, "type": "monthly", "features": ["2 vCPU", "4 GB RAM"]},
            {"name": "Azure D2s v3", "price": 70.08, "type": "monthly", "features": ["2 vCPU", "8 GB RAM"]},
         ]},
        {"name": "DigitalOcean", "website": "digitalocean.com", "tier": "budget", "market_share": 5,
         "products": [
            {"name": "DO Basic 1GB", "price": 6.00, "type": "monthly", "features": ["1 vCPU", "1 GB RAM", "25 GB SSD"]},
            {"name": "DO Basic 4GB", "price": 24.00, "type": "monthly", "features": ["2 vCPU", "4 GB RAM", "80 GB SSD"]},
            {"name": "DO Basic 8GB", "price": 48.00, "type": "monthly", "features": ["4 vCPU", "8 GB RAM", "160 GB SSD"]},
         ]},
        {"name": "Vultr", "website": "vultr.com", "tier": "budget", "market_share": 3,
         "products": [
            {"name": "Vultr Cloud 1GB", "price": 5.00, "type": "monthly", "features": ["1 vCPU", "1 GB RAM", "25 GB SSD"]},
            {"name": "Vultr Cloud 4GB", "price": 20.00, "type": "monthly", "features": ["2 vCPU", "4 GB RAM", "80 GB SSD"]},
            {"name": "Vultr Cloud 8GB", "price": 40.00, "type": "monthly", "features": ["4 vCPU", "8 GB RAM", "160 GB SSD"]},
         ]},
    ],
    "Email Marketing": [
        {"name": "Mailchimp", "website": "mailchimp.com", "tier": "mid-range", "market_share": 25,
         "products": [
            {"name": "Mailchimp Essentials", "price": 13.00, "type": "monthly", "features": ["email templates", "A/B testing", "500 contacts"]},
            {"name": "Mailchimp Standard", "price": 20.00, "type": "monthly", "features": ["automation", "retargeting", "2500 contacts"]},
            {"name": "Mailchimp Premium", "price": 350.00, "type": "monthly", "features": ["advanced segmentation", "multivariate testing", "10K contacts"]},
         ]},
        {"name": "ConvertKit", "website": "convertkit.com", "tier": "mid-range", "market_share": 10,
         "products": [
            {"name": "ConvertKit Creator", "price": 15.00, "type": "monthly", "features": ["unlimited landing pages", "email broadcasts", "300 subs"]},
            {"name": "ConvertKit Creator Pro", "price": 29.00, "type": "monthly", "features": ["automation", "scoring", "newsletter referral", "300 subs"]},
         ]},
        {"name": "SendGrid", "website": "sendgrid.com", "tier": "budget", "market_share": 15,
         "products": [
            {"name": "SendGrid Essentials", "price": 19.95, "type": "monthly", "features": ["50K emails/mo", "APIs", "webhooks"]},
            {"name": "SendGrid Pro", "price": 89.95, "type": "monthly", "features": ["100K emails/mo", "dedicated IP", "sub-user management"]},
         ]},
        {"name": "ActiveCampaign", "website": "activecampaign.com", "tier": "mid-range", "market_share": 12,
         "products": [
            {"name": "AC Starter", "price": 15.00, "type": "monthly", "features": ["email marketing", "automation", "inline forms"]},
            {"name": "AC Plus", "price": 49.00, "type": "monthly", "features": ["CRM", "lead scoring", "landing pages"]},
            {"name": "AC Professional", "price": 79.00, "type": "monthly", "features": ["site messaging", "attribution", "split automations"]},
         ]},
    ],
    "Analytics & BI": [
        {"name": "Tableau", "website": "tableau.com", "tier": "enterprise", "market_share": 20,
         "products": [
            {"name": "Tableau Creator", "price": 75.00, "type": "per-user/mo", "features": ["data prep", "visual analytics", "data management"]},
            {"name": "Tableau Explorer", "price": 42.00, "type": "per-user/mo", "features": ["self-service analytics", "governed data"]},
            {"name": "Tableau Viewer", "price": 15.00, "type": "per-user/mo", "features": ["view dashboards", "subscribe to reports"]},
         ]},
        {"name": "Power BI", "website": "powerbi.microsoft.com", "tier": "mid-range", "market_share": 25,
         "products": [
            {"name": "Power BI Pro", "price": 10.00, "type": "per-user/mo", "features": ["reports", "dashboards", "collaboration"]},
            {"name": "Power BI Premium Per User", "price": 20.00, "type": "per-user/mo", "features": ["AI insights", "dataflows", "paginated reports"]},
         ]},
        {"name": "Looker", "website": "looker.com", "tier": "enterprise", "market_share": 10,
         "products": [
            {"name": "Looker Standard", "price": 60.00, "type": "per-user/mo", "features": ["data modeling", "SQL IDE", "dashboards"]},
            {"name": "Looker Enterprise", "price": 125.00, "type": "per-user/mo", "features": ["embedded analytics", "API", "custom roles"]},
         ]},
        {"name": "Metabase", "website": "metabase.com", "tier": "budget", "market_share": 8,
         "products": [
            {"name": "Metabase Starter", "price": 0.00, "type": "monthly", "features": ["open-source", "SQL queries", "dashboards"]},
            {"name": "Metabase Pro", "price": 85.00, "type": "monthly", "features": ["SSO", "audit logs", "serialization"]},
         ]},
        {"name": "Mixpanel", "website": "mixpanel.com", "tier": "mid-range", "market_share": 8,
         "products": [
            {"name": "Mixpanel Growth", "price": 25.00, "type": "monthly", "features": ["unlimited reports", "data modeling", "group analytics"]},
            {"name": "Mixpanel Enterprise", "price": 833.00, "type": "monthly", "features": ["SSO", "advanced access", "data pipeline"]},
         ]},
    ],
}

DEMO_MARKET_EVENTS = [
    {"title": "Salesforce raises enterprise tier by 9%", "description": "Annual price increase affects Enterprise and Unlimited editions", "event_type": "price_increase", "category": "CRM Software", "days_ago": 15},
    {"title": "ClickUp launches free tier expansion", "description": "Now includes unlimited tasks and 100MB storage for free users", "event_type": "product_launch", "category": "Project Management", "days_ago": 22},
    {"title": "AWS announces 15% price cut on EC2 instances", "description": "Across-the-board reduction to compete with Azure and GCP", "event_type": "price_war", "category": "Cloud Hosting", "days_ago": 30},
    {"title": "Mailchimp acquired by Intuit for $12B", "description": "Integration with QuickBooks ecosystem expected", "event_type": "acquisition", "category": "Email Marketing", "days_ago": 60},
    {"title": "Metabase raises $30M Series B", "description": "Plans to expand enterprise features and challenge Tableau", "event_type": "funding", "category": "Analytics & BI", "days_ago": 45},
    {"title": "Monday.com introduces AI assistant features", "description": "AI-powered automation and workflow suggestions across all tiers", "event_type": "product_launch", "category": "Project Management", "days_ago": 10},
    {"title": "HubSpot slashes Starter CRM price by 40%", "description": "Aggressive push to capture SMB market from Salesforce", "event_type": "price_war", "category": "CRM Software", "days_ago": 8},
]


async def seed_demo_data(db):
    """Seed the database with realistic competitive pricing data."""
    from sqlalchemy import select

    result = await db.execute(select(Category))
    if result.scalars().first():
        return {"message": "Data already seeded"}

    # Create categories
    cat_map = {}
    for cat_data in DEMO_CATEGORIES:
        cat = Category(**cat_data)
        db.add(cat)
        await db.flush()
        cat_map[cat.name] = cat.id

    # Create competitors, products, price points
    total_products = 0
    total_prices = 0
    total_alerts = 0

    for cat_name, competitors in DEMO_COMPETITORS.items():
        cat_id = cat_map[cat_name]
        for comp_data in competitors:
            comp = Competitor(
                name=comp_data["name"],
                website=comp_data["website"],
                category_id=cat_id,
                tier=comp_data["tier"],
                market_share_pct=comp_data["market_share"],
            )
            db.add(comp)
            await db.flush()

            for prod_data in comp_data["products"]:
                product = Product(
                    competitor_id=comp.id,
                    name=prod_data["name"],
                    sku=f"SKU-{comp.id}-{total_products}",
                    category_id=cat_id,
                    features=json.dumps(prod_data["features"]),
                )
                db.add(product)
                await db.flush()
                total_products += 1

                # Generate 12 months of price history with realistic fluctuation
                base_price = prod_data["price"]
                for month_offset in range(12):
                    date = datetime.utcnow() - timedelta(days=30 * (11 - month_offset) + random.randint(0, 5))
                    # Simulate gradual price changes
                    drift = random.uniform(-0.05, 0.08) * month_offset * 0.1
                    noise = random.uniform(-0.03, 0.03)
                    price = max(0, round(base_price * (1 + drift + noise), 2))
                    
                    original_price = None
                    if random.random() < 0.15:
                        original_price = round(price * random.uniform(1.1, 1.3), 2)
                    
                    pp = PricePoint(
                        product_id=product.id,
                        competitor_id=comp.id,
                        price=price,
                        original_price=original_price,
                        currency="USD",
                        price_type=prod_data["type"],
                        recorded_at=date,
                    )
                    db.add(pp)
                    total_prices += 1

                    # Generate alerts for significant changes
                    if month_offset > 0 and abs(drift) > 0.03:
                        alert = PriceAlert(
                            product_id=product.id,
                            competitor_id=comp.id,
                            alert_type="price_increase" if drift > 0 else "price_drop",
                            old_price=round(base_price * (1 + drift * 0.8), 2),
                            new_price=price,
                            change_pct=round(drift * 100, 1),
                            message=f"{comp.name} {'raised' if drift > 0 else 'dropped'} {prod_data['name']} price",
                            created_at=date,
                        )
                        db.add(alert)
                        total_alerts += 1

    # Market events
    for ev_data in DEMO_MARKET_EVENTS:
        cat_id = cat_map.get(ev_data["category"])
        event = MarketEvent(
            title=ev_data["title"],
            description=ev_data["description"],
            event_type=ev_data["event_type"],
            category_id=cat_id,
            event_date=datetime.utcnow() - timedelta(days=ev_data["days_ago"]),
        )
        db.add(event)

    await db.commit()
    return {"message": f"Seeded {len(DEMO_CATEGORIES)} categories, {total_products} products, {total_prices} price points, {total_alerts} alerts"}
