def clean_review(review_text: str) -> str:
    cleaned = review_text.lower()
    cleaned = " ".join(cleaned.split())
    return cleaned


def chunkers(reviews_or_prompt, chunk_size: int = 200) -> list[list[str]]:
    # Unifies chunking of both list of reviews (for routers) and newline-separated prompt strings (for services)
    if isinstance(reviews_or_prompt, str):
        raw_reviews = [line.strip() for line in reviews_or_prompt.split("\n") if line.strip()]
    else:
        raw_reviews = reviews_or_prompt

    if not raw_reviews:
        return [["No reviews provided."]]

    cleaned_reviews = [clean_review(review) for review in raw_reviews]
    chunks = [
        cleaned_reviews[i : i + chunk_size]
        for i in range(0, len(cleaned_reviews), chunk_size)
    ]

    return chunks
