MULTI_QUERY_PROMPT = """
You generate alternative search queries for a RAG retrieval system.

Original query:
{question}

Generate 3 alternative queries that search for the SAME information
as the original query.

Rules:

1. Preserve the exact information need.
2. Do NOT ask a different question.
3. Do NOT broaden the topic.
4. Do NOT invent facts.
5. Do NOT introduce architecture, implementation,
   examples, causes, outcomes, or related topics unless
   they are explicitly part of the original question.
6. Use different wording, synonyms, or search-oriented phrasing.
7. Each query must independently retrieve evidence that could answer
   the original question.
8. Return ONLY the queries, one per line.
"""