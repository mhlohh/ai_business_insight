def clean_review(review_text: str):
    cleaned = review_text.lower()
    cleaned = " ".join(cleaned.split())
    return cleaned


def chunkers(raw_reviews, chunk_size: int = 200) -> list[list[str]]:
    # If a single prompt string is passed (e.g. from analysis_service ask/ask_stream), split it by newlines
    if isinstance(raw_reviews, str):
        reviews_list = [line.strip() for line in raw_reviews.split("\n") if line.strip()]
    else:
        reviews_list = raw_reviews

    if not reviews_list:
        return [["No reviews provided."]]

    cleaned_reviews = [clean_review(review) for review in reviews_list]
    chunks = [
        cleaned_reviews[i : i + chunk_size]
        for i in range(0, len(cleaned_reviews), chunk_size)
    ]

    return chunks
