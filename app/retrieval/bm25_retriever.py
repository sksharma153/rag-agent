import os
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class BM25Retriever:

    def __init__(
            self,
            index_path: str | None = None,
    ):
        if index_path is None:
            index_path = str(
                PROJECT_ROOT / "data" / "bm25"
            )

        self.index_path = index_path
        self.tenant_indexes = {}

        os.makedirs(self.index_path, exist_ok=True)
        self._load()

    def add_chunks(
            self,
            tenant_id: str,
            chunks: list
    ):

        tokenized_documents = [
            chunk.text.lower().split()
            for chunk in chunks
        ]

        bm25 = BM25Okapi(tokenized_documents)

        self.tenant_indexes[tenant_id] = {
            "bm25": bm25,
            "chunks": chunks
        }

        self._save(tenant_id)

    def search(
            self,
            tenant_id: str,
            query: str,
            document_id: str | None = None,
            k: int = 5,
    ):
        index = self.tenant_indexes.get(tenant_id)

        if not index:
            return []

        bm25 = index["bm25"]
        chunks = index["chunks"]
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # ---------------------------------
        # Determine which chunks to search
        # ---------------------------------

        candidate_indexes = []
        for i, chunk in enumerate(chunks):
            if document_id is None:
                # Search all documents for this tenant
                candidate_indexes.append(i)
            else:
                chunk_document_id = chunk.metadata.get(
                    "document_id"
                )
                if chunk_document_id == document_id:
                    candidate_indexes.append(i)

        # ---------------------------------
        # Rank only candidate chunks
        # ---------------------------------

        ranked_indexes = sorted(
            candidate_indexes,
            key=lambda i: scores[i],
            reverse=True,
        )[:k]

        # ---------------------------------
        # Build results
        # ---------------------------------

        results = []

        for index in ranked_indexes:
            results.append({
                "chunk": chunks[index],
                "score": float(scores[index]),
            })

        return results

    def _save(
            self,
            tenant_id: str
    ):
        path = os.path.join(self.index_path, f"{tenant_id}.pkl")
        with open(path, "wb") as file:
            pickle.dump(
                self.tenant_indexes[tenant_id],
                file
            )

    def _load(self):
        for filename in os.listdir(self.index_path):
            if not filename.endswith(".pkl"):
                continue

            tenant_id = filename[:-4]

            path = os.path.join(self.index_path, filename)
            
            try:
                with open(path, "rb") as file:
                    self.tenant_indexes[tenant_id] = pickle.load(file)

                print(f"Loaded BM25 index: {tenant_id}")

            except Exception as e:
                print(f"Failed to load BM25 index: {tenant_id}: {e}")