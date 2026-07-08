def clean_review(review_text:str):
    cleaned = review_text.lower()
    cleaned = " ".join(cleaned.split())
    return cleaned

def chunkers(raw_reviews: list[str], chunk_size: int = 100) -> list[list[str]]:
    cleaned_reviews = [clean_review(review) for review in raw_reviews]
    chunks = [cleaned_reviews[i:i + chunk_size] for i in range(0, len(cleaned_reviews), chunk_size)]
    
    return chunks
