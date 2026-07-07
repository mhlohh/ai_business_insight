import os


def chunk_reviews(prompt: str) -> list[list[str]]:
    """
    Helper to chunk a large block of reviews (each review on a separate line)
    into smaller sub-lists of reviews.
    """
    lines = [line.strip() for line in prompt.split("\n") if line.strip()]
    if not lines:
        return [["No reviews provided."]]

    # Cap total reviews to analyze for performance and context limits of local models
    max_reviews = int(os.getenv("MAX_REVIEWS_TO_ANALYZE", "100"))
    lines = lines[:max_reviews]

    # Dynamically select a chunk size based on input size
    if len(lines) < 10:
        chunk_size = 3
    elif len(lines) < 100:
        chunk_size = 10
    else:
        chunk_size = 20  # 5 chunks of 20 reviews for max 100

    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunks.append(lines[i : i + chunk_size])
    return chunks
