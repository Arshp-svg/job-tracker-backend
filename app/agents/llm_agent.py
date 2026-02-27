def generate_insight_summary(rejection_insights):
    """
    rejection_insights: list of dicts
    Example:
    [{"company": "Google", "rejections": 2}]
    """

    if not rejection_insights:
        return "You have no rejection patterns yet."

    summaries = []
    for item in rejection_insights:
        summaries.append(
            f"You were rejected {item['rejections']} times at {item['company']}."
        )

    return " ".join(summaries)
