"""Sentiment analysis engine using VADER + TextBlob ensemble."""
import json
import re
from typing import Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

# Initialize VADER
vader = SentimentIntensityAnalyzer()

# Topic keywords mapping
TOPIC_KEYWORDS = {
    "culture": ["culture", "environment", "atmosphere", "vibe", "team", "colleagues", "coworkers", "fun", "toxic", "inclusive", "diverse"],
    "compensation": ["pay", "salary", "compensation", "bonus", "stock", "equity", "benefits", "401k", "raise", "underpaid", "overpaid"],
    "leadership": ["management", "leadership", "ceo", "executive", "manager", "boss", "director", "vp", "c-suite", "founder"],
    "work_life_balance": ["work-life", "balance", "hours", "overtime", "flexible", "remote", "wfh", "hybrid", "burnout", "vacation", "pto"],
    "career_growth": ["growth", "promotion", "career", "learning", "development", "training", "advancement", "mentorship", "opportunity"],
    "dei": ["diversity", "inclusion", "equity", "dei", "belonging", "representation", "discrimination", "bias", "equal"],
    "technology": ["technology", "tech", "tools", "stack", "engineering", "software", "innovation", "legacy", "modern"],
    "job_security": ["layoff", "fired", "restructuring", "downsizing", "stability", "secure", "uncertain", "rif"],
    "onboarding": ["onboarding", "training", "ramp-up", "orientation", "new hire", "first day"],
    "benefits": ["health", "insurance", "dental", "vision", "parental", "leave", "perks", "free food", "gym"],
}


def analyze_sentiment(text: Optional[str]) -> float:
    """Analyze sentiment using VADER + TextBlob ensemble. Returns -1 to 1."""
    if not text or not text.strip():
        return 0.0

    # VADER score
    vader_scores = vader.polarity_scores(text)
    vader_compound = vader_scores["compound"]

    # TextBlob score (already -1 to 1)
    blob = TextBlob(text)
    textblob_score = blob.sentiment.polarity

    # Ensemble: weighted average (VADER is better for social/review text)
    return round(vader_compound * 0.6 + textblob_score * 0.4, 4)


def extract_topics(text: Optional[str]) -> list[str]:
    """Extract topics from review text based on keyword matching."""
    if not text:
        return []

    text_lower = text.lower()
    found_topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_topics.append(topic)
                break

    return found_topics


def classify_sentiment(score: float) -> str:
    """Classify a sentiment score into positive/negative/neutral."""
    if score > 0.05:
        return "positive"
    elif score < -0.05:
        return "negative"
    return "neutral"


def analyze_review(title: str = "", pros: str = "", cons: str = "", review_text: str = "") -> dict:
    """Full analysis of a review. Returns sentiment scores + topics."""
    # Combine all text for topic extraction
    full_text = f"{title} {pros} {cons} {review_text}".strip()

    # Analyze each section
    pros_sentiment = analyze_sentiment(pros)
    cons_sentiment = analyze_sentiment(cons)

    # Overall: weighted combination
    if pros and cons:
        overall = analyze_sentiment(full_text)
    elif pros:
        overall = pros_sentiment
    elif cons:
        overall = cons_sentiment
    else:
        overall = analyze_sentiment(review_text or title)

    topics = extract_topics(full_text)

    return {
        "overall_sentiment": overall,
        "pros_sentiment": pros_sentiment,
        "cons_sentiment": cons_sentiment,
        "classification": classify_sentiment(overall),
        "topics": topics,
    }
