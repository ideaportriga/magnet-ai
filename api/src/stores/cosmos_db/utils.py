from decimal import Decimal


def cosine_similarity_to_distance_score(score_similarity: Decimal) -> Decimal:
    """Convert cosine similarity to cosine distance.

    Parameters
    ----------
    - score_similarity (float): Cosine similarity score between two vectors.

    Returns
    -------
    - float: Cosine distance score, ranging from 0 (perfect similarity) to 2 (perfect dissimilarity).

    The function transforms a cosine similarity score to its corresponding cosine distance score.

    For more information on cosine similarity, see:
    https://en.wikipedia.org/wiki/Cosine_similarity

    """
    score_distance = Decimal(1) - score_similarity

    return score_distance
