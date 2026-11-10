import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Plan, Subscriber, Activity, RevenueMetric, ChurnReason

PLANS = [
    ("Free", 0, "free"),
    ("Starter", 29, "starter"),
    ("Pro", 79, "pro"),
    ("Business", 199, "business"),
    ("Enterprise", 499, "enterprise"),
]

COMPANIES = [
    "Acme Corp", "TechFlow", "DataVista", "CloudPeak", "NexGen Solutions",
    "BrightPath", "Quantum Labs", "Pinnacle Inc", "Forge Digital", "Summit AI",
    "Velocity SaaS", "BlueShift", "Atlas Group", "Synapse Co", "Prism Analytics",
    "Orbit Tech", "Zenith Corp", "Catalyst Inc", "Mosaic Digital", "Apex Systems",
    "Ridge Analytics", "Nova Soft", "Cipher Logic", "Titan Services", "Helix Data",
]

CHURN_REASONS = [
    ("Too expensive", "pricing", 45),
    ("Switched to competitor", "competition", 38),
    ("Missing features", "product", 32),
    ("Poor customer support", "support", 28),
    ("Not enough ROI", "value", 25),
    ("Company downsizing", "external", 20),
    ("Too complex to use", "usability", 18),
    ("Integration issues", "technical", 15),
    ("Budget cuts", "external", 12),
    ("Outgrew the product", "product", 10),
]


async def seed_data(session: AsyncSession):
    random.seed(42)

    # Create plans
    plans = []
    for name, price, tier in PLANS:
        p = Plan(name=name, price_monthly=price, tier=tier)
        session.add(p)
        plans.append(p)
    await session.flush()

    # Create subscribers (800 total, ~15% churned)
    subscribers = []
    base_date = datetime(2024, 4, 1)
    for i in range(800):
        plan = random.choices(plans, weights=[15, 30, 25, 20, 10])[0]
        signup = base_date + timedelta(days=random.randint(0, 365))
        is_churned = random.random() < 0.15
        churn_date = signup + timedelta(days=random.randint(30, 300)) if is_churned else None
        if churn_date and churn_date > datetime(2025, 4, 1):
            churn_date = None
            is_churned = False

        usage = random.uniform(10, 95) if not is_churned else random.uniform(5, 40)
        health = random.uniform(20, 95) if not is_churned else random.uniform(5, 35)
        risk = random.uniform(0.01, 0.7) if not is_churned else random.uniform(0.6, 1.0)
        ltv = plan.price_monthly * random.randint(3, 24)
        nps = random.choice([random.randint(7, 10), random.randint(1, 6), random.randint(0, 4)]) if random.random() > 0.3 else None

        sub = Subscriber(
            email=f"user{i}@{random.choice(['gmail.com','company.com','outlook.com','work.io'])}",
            company=random.choice(COMPANIES),
            plan_id=plan.id, signup_date=signup, churn_date=churn_date,
            is_churned=is_churned, mrr=plan.price_monthly,
            lifetime_value=ltv, usage_score=round(usage, 1),
            health_score=round(health, 1), churn_risk=round(risk, 3),
            last_login_days=random.randint(0, 7) if not is_churned else random.randint(14, 90),
            support_tickets=random.randint(0, 8),
            feature_adoption=round(random.uniform(15, 90) if not is_churned else random.uniform(5, 30), 1),
            nps_score=nps
        )
        session.add(sub)
        subscribers.append(sub)
    await session.flush()

    # Activity per subscriber per month (last 6 months)
    for sub in subscribers:
        for m in range(6):
            month_date = datetime(2024, 10 + m if m < 3 else m - 2, 1) if m < 3 else datetime(2025, m - 2, 1)
            month_str = month_date.strftime("%Y-%m")
            base_engagement = sub.usage_score / 100
            act = Activity(
                subscriber_id=sub.id, month=month_str,
                logins=int(random.uniform(1, 30) * base_engagement),
                api_calls=int(random.uniform(10, 5000) * base_engagement),
                features_used=int(random.uniform(1, 15) * base_engagement),
                support_tickets=random.randint(0, 3),
                engagement_score=round(random.uniform(20, 95) * base_engagement, 1)
            )
            session.add(act)
    await session.flush()

    # Revenue metrics (12 months)
    base_mrr = 45000
    for m in range(12):
        month_date = datetime(2024, 5, 1) + timedelta(days=30 * m)
        month_str = month_date.strftime("%Y-%m")
        growth = 1 + random.uniform(0.02, 0.08)
        churn_pct = random.uniform(0.03, 0.07)
        new_mrr = base_mrr * random.uniform(0.08, 0.15)
        churned = base_mrr * churn_pct
        expansion = base_mrr * random.uniform(0.02, 0.06)
        net = new_mrr - churned + expansion
        base_mrr = base_mrr + net

        active = 680 + m * random.randint(5, 20)
        new_subs = random.randint(30, 80)
        churned_subs = random.randint(8, 25)

        rm = RevenueMetric(
            month=month_str, mrr=round(base_mrr, 2),
            new_mrr=round(new_mrr, 2), churned_mrr=round(churned, 2),
            expansion_mrr=round(expansion, 2), net_mrr=round(net, 2),
            active_subscribers=active, new_subscribers=new_subs,
            churned_subscribers=churned_subs,
            churn_rate=round(churned_subs / active * 100, 2),
            revenue_churn_rate=round(churn_pct * 100, 2)
        )
        session.add(rm)

    # Churn reasons
    for reason, category, count in CHURN_REASONS:
        cr = ChurnReason(
            reason=reason, count=count,
            revenue_lost=round(count * random.uniform(79, 350), 2),
            category=category
        )
        session.add(cr)

    await session.commit()
    print(f"Seeded: {len(plans)} plans, {len(subscribers)} subscribers, {len(subscribers)*6} activities, 12 revenue months, {len(CHURN_REASONS)} churn reasons")
