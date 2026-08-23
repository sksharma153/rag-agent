def hit_rate_at_k(
        retrieved_ids: list[str],
        relevant_ids: set[str],
        k: int,
) -> float:
    top_k = retrieved_ids[:k]

    return float(
        any(chunk_id in relevant_ids for chunk_id in top_k)
    )

def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    top_k = retrieved_ids[:k]

    if not top_k:
        return 0.0

    relevant_count = sum(
        1 for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_count / len(top_k)

def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int
) -> float:
    if not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]

    relevant_count = sum(
        1 for chunk_id in relevant_ids
        if chunk_id in top_k
    )

    return relevant_count / len(relevant_ids)

def reciprocal_rank(
        retrieved_ids: list[str],
        relevant_ids: set[str],
) -> float:

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1.0 / rank

    return 0.0

def mean_reciprocal_rank(
    reciprocal_ranks: list[float],
) -> float:

    if not reciprocal_rank:
        return 0.0

    return sum(reciprocal_ranks) / len(reciprocal_ranks)