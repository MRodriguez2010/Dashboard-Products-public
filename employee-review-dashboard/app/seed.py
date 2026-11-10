"""Generate realistic demo data for the ESA Dashboard."""
import json
import random
from datetime import datetime, timedelta
from app.models import Company, Review, Event
from app.sentiment import analyze_review

# Realistic company data
DEMO_COMPANIES = [
    {"name": "TechVault Inc", "industry": "Technology", "size": "5000-10000"},
    {"name": "GreenLeaf Health", "industry": "Healthcare", "size": "1000-5000"},
    {"name": "FinCore Systems", "industry": "Financial Services", "size": "10000+"},
    {"name": "NovaByte AI", "industry": "Technology", "size": "100-500"},
    {"name": "Meridian Consulting", "industry": "Consulting", "size": "500-1000"},
    {"name": "CloudPeak Solutions", "industry": "Technology", "size": "1000-5000"},
    {"name": "Apex Retail Group", "industry": "Retail", "size": "10000+"},
    {"name": "DataStream Analytics", "industry": "Technology", "size": "100-500"},
]

ROLES = [
    "Software Engineer", "Senior Developer", "Data Analyst", "Product Manager",
    "DevOps Engineer", "UX Designer", "Marketing Manager", "Sales Rep",
    "HR Specialist", "Customer Success", "QA Engineer", "Data Scientist",
    "Technical Lead", "Engineering Manager", "Business Analyst",
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA",
    "Denver, CO", "Chicago, IL", "Boston, MA", "Remote", "London, UK",
    "Toronto, Canada", "Bangalore, India",
]

# Review templates - realistic pros/cons
REVIEW_TEMPLATES = [
    # Positive reviews
    {"title": "Great culture and smart people", "pros": "Amazing team culture, everyone is supportive and collaborative. Leadership is transparent about company direction. Great work-life balance with flexible remote policy. Excellent benefits including unlimited PTO and equity.", "cons": "Career growth can be slow in some departments. Technology stack could use modernization in a few areas.", "rating": 4.5},
    {"title": "Best place I've worked", "pros": "Incredible engineering culture. Management truly cares about employee development. Competitive salary and stock options. Free lunch and great office perks. Learning and development budget is generous.", "cons": "Sometimes too many meetings. Can be hard to transfer between teams.", "rating": 5.0},
    {"title": "Solid company with good values", "pros": "Strong commitment to diversity and inclusion. Good work-life balance. Decent pay and benefits. Interesting projects with modern technology. Mentorship program is excellent for career growth.", "cons": "Promotion process is opaque. Some legacy systems are frustrating to work with.", "rating": 4.0},
    {"title": "Great for learning and growing", "pros": "Tons of learning opportunities. Leadership encourages innovation. Good compensation package. Flexible work from home policy. Inclusive and diverse environment.", "cons": "Fast pace can be stressful sometimes. Onboarding could be better organized.", "rating": 4.0},
    {"title": "Innovation at its finest", "pros": "Cutting-edge technology stack. Smart colleagues who push you to be better. Good salary with annual bonuses. Company is growing fast with exciting vision.", "cons": "Work hours can get long during crunch times. Benefits could be more competitive.", "rating": 4.5},

    # Mixed reviews
    {"title": "Good company but room for improvement", "pros": "Decent salary and some good people to work with. Technology is interesting.", "cons": "Management needs improvement. Work-life balance is inconsistent. Career growth opportunities are limited for some teams. DEI efforts feel performative.", "rating": 3.0},
    {"title": "Average experience overall", "pros": "Pay is competitive. Some teams have great culture. Benefits are okay.", "cons": "Leadership lacks direction. Too much bureaucracy. Layoff rumors create job insecurity. Training and onboarding are nonexistent.", "rating": 3.0},
    {"title": "Depends heavily on your team", "pros": "Some teams are great with supportive managers. Technology is modern. Office perks are nice.", "cons": "Huge variance between teams. Some managers are terrible. No clear career path. Compensation reviews feel arbitrary.", "rating": 2.5},
    {"title": "Used to be great, declining", "pros": "Brand name still carries weight. Smart people still work here. Technology foundation is solid.", "cons": "Culture has deteriorated since new leadership. Layoffs have destroyed trust. Benefits keep getting cut. Morale is at an all-time low. Work-life balance is non-existent.", "rating": 2.0},

    # Negative reviews
    {"title": "Toxic management, avoid", "pros": "The pay is okay. Some good individual contributors.", "cons": "Toxic leadership culture. Management plays favorites. No work-life balance whatsoever. Burnout is normalized. Diversity is just a talking point, not reality. People are being laid off while executives get bonuses.", "rating": 1.5},
    {"title": "Run away while you can", "pros": "Free snacks I guess.", "cons": "Terrible management that micromanages everything. No career growth. Salary is below market. Benefits are the bare minimum. Culture of fear and intimidation. High turnover for obvious reasons.", "rating": 1.0},
    {"title": "Disappointing experience", "pros": "Learned what NOT to do in management.", "cons": "Leadership is completely disconnected. Technology is outdated legacy systems. Pay is below market average. Job security is nonexistent with constant restructuring. Onboarding is basically thrown in the deep end.", "rating": 1.5},
]

DEMO_EVENTS = [
    {"event_type": "layoff", "title": "TechVault announces 15% workforce reduction", "description": "Company-wide layoffs affecting engineering and marketing teams", "company_idx": 0, "days_ago": 45},
    {"event_type": "policy_change", "title": "FinCore mandates return to office 4 days/week", "description": "New RTO policy effective immediately, employee backlash expected", "company_idx": 2, "days_ago": 30},
    {"event_type": "earnings", "title": "NovaByte AI reports 200% revenue growth", "description": "Strong Q4 results drive stock up 30%", "company_idx": 3, "days_ago": 15},
    {"event_type": "merger", "title": "CloudPeak acquired by enterprise giant for $2B", "description": "Major acquisition raises questions about culture preservation", "company_idx": 5, "days_ago": 60},
    {"event_type": "policy_change", "title": "GreenLeaf launches 4-day work week pilot", "description": "Healthcare company testing reduced hours for better employee wellbeing", "company_idx": 1, "days_ago": 20},
    {"event_type": "layoff", "title": "Apex Retail closes 50 stores, cuts 2000 jobs", "description": "Retail restructuring amid shifting consumer habits", "company_idx": 6, "days_ago": 90},
]


async def seed_demo_data(db):
    """Seed the database with realistic demo data."""
    from sqlalchemy import select

    # Check if data already exists
    result = await db.execute(select(Company))
    if result.scalars().first():
        return {"message": "Data already seeded"}

    # Create companies
    companies = []
    for co_data in DEMO_COMPANIES:
        company = Company(**co_data)
        db.add(company)
        companies.append(company)
    await db.flush()

    # Generate reviews — ~40-80 per company, spread over last 12 months
    total_reviews = 0
    for company in companies:
        num_reviews = random.randint(40, 80)
        for _ in range(num_reviews):
            template = random.choice(REVIEW_TEMPLATES)
            # Add some variation
            review_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))

            analysis = analyze_review(
                title=template["title"],
                pros=template["pros"],
                cons=template["cons"],
            )

            review = Review(
                company_id=company.id,
                source=random.choice(["glassdoor", "indeed", "glassdoor", "internal"]),
                title=template["title"],
                pros=template["pros"],
                cons=template["cons"],
                rating=template["rating"] + random.uniform(-0.5, 0.5),
                reviewer_role=random.choice(ROLES),
                reviewer_location=random.choice(LOCATIONS),
                is_current_employee=random.choice(["yes", "yes", "no"]),
                review_date=review_date,
                overall_sentiment=analysis["overall_sentiment"],
                pros_sentiment=analysis["pros_sentiment"],
                cons_sentiment=analysis["cons_sentiment"],
                topics=json.dumps(analysis["topics"]),
            )
            # Clamp rating to 1-5
            review.rating = max(1.0, min(5.0, round(review.rating, 1)))
            db.add(review)
            total_reviews += 1

    # Create events
    for ev_data in DEMO_EVENTS:
        event = Event(
            company_id=companies[ev_data["company_idx"]].id,
            event_type=ev_data["event_type"],
            title=ev_data["title"],
            description=ev_data["description"],
            event_date=datetime.utcnow() - timedelta(days=ev_data["days_ago"]),
        )
        db.add(event)

    await db.commit()
    return {"message": f"Seeded {len(companies)} companies, {total_reviews} reviews, {len(DEMO_EVENTS)} events"}
