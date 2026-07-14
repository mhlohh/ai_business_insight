import os


def clean_review(review_text: str) -> str:
    cleaned = review_text.lower()
    cleaned = " ".join(cleaned.split())
    return cleaned


def chunkers(prompt: str, chunk_size: int = 200) -> list[list[str]]:
    # Helper to chunk a large block of reviews into smaller sub-lists.
    lines = [line.strip() for line in prompt.split("\n") if line.strip()]
    if not lines:
        return [["No reviews provided."]]

    cleaned_reviews = [clean_review(review) for review in lines]
    chunks = [
        cleaned_reviews[i : i + chunk_size]
        for i in range(0, len(cleaned_reviews), chunk_size)
    ]

    return chunks
