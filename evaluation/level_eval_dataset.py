import json
from pathlib import Path


INPUT_FILE = Path("retrieval_candidates.json")
OUTPUT_FILE = Path("eval_database_gold.json")

def normalize_chunk_id(value: str) -> str:
    return value.strip().strip('"').strip("'")


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    gold_dataset = []

    for index, item in enumerate(dataset, start=1):

        print("\n" + "=" * 100)
        print(f"QUESTION {index}/{len(dataset)}")
        print("=" * 100)

        print("\nQuestion:")
        print(item["question"])

        print("\nExpected Answer:")
        print(item.get("expected_answer", "N/A"))

        candidates = item.get("candidates", [])

        if not candidates:
            print("\nNO CANDIDATES FOUND")
            print("Skipping this question.")
            continue

        print("\nCandidates:")

        candidate_by_rank = {}
        candidate_by_id = {}

        for candidate in candidates:

            rank = candidate["rank"]
            chunk_id = candidate["chunk_id"]

            candidate_by_rank[rank] = candidate
            candidate_by_id[chunk_id] = candidate

            print("\n" + "-" * 100)
            print(f"Rank      : {rank}")
            print(f"Chunk ID   : {chunk_id}")
            print(
                f"Hybrid    : "
                f"{candidate.get('hybrid_score', 0.0)}"
            )
            print("Text:")
            print(candidate["text"][:2500])

        print("\n" + "=" * 100)
        print("Enter relevant RANKS or CHUNK IDs.")
        print("Examples:")
        print("  1,3")
        print("  1")
        print("  b06a4b5e-...:113")
        print("  1,b06a4b5e-...:113")
        print("Enter 's' to skip.")
        print("Enter 'none' if no candidate is relevant.")

        user_input = input(
            "\nRelevant chunks: "
        ).strip()

        relevant_chunk_ids = []

        if user_input.lower() not in {
            "s",
            "skip",
            "none",
            "",
        }:

            values = [
                normalize_chunk_id(x)
                for x in user_input.split(",")
                if x.strip()
            ]

            for value in values:

                # -----------------------------
                # User entered a rank
                # -----------------------------
                if value.isdigit():

                    rank = int(value)

                    candidate = candidate_by_rank.get(
                        rank
                    )

                    if candidate:

                        chunk_id = candidate[
                            "chunk_id"
                        ]

                        if chunk_id not in relevant_chunk_ids:
                            relevant_chunk_ids.append(
                                chunk_id
                            )

                        print(
                            f"Selected rank {rank}: "
                            f"{chunk_id}"
                        )

                    else:

                        print(
                            f"WARNING: rank {rank} "
                            f"does not exist."
                        )

                # -----------------------------
                # User entered a chunk ID
                # -----------------------------
                else:

                    if value in candidate_by_id:

                        if value not in relevant_chunk_ids:
                            relevant_chunk_ids.append(
                                value
                            )

                        print(
                            f"Selected chunk: {value}"
                        )

                    else:

                        print(
                            f"WARNING: chunk ID not "
                            f"found in candidates: {value}"
                        )

        # -----------------------------------------
        # Build gold record
        # -----------------------------------------

        gold_item = {
            "id": item["id"],
            "question": item["question"],
            "expected_answer": item.get(
                "expected_answer"
            ),
            "document_id": item[
                "document_id"
            ],
            "source_pages": item.get(
                "source_pages",
                [],
            ),
            "relevant_chunk_ids":
                relevant_chunk_ids,
        }

        gold_dataset.append(gold_item)

        print("\nSELECTED CHUNK IDS:")

        if relevant_chunk_ids:

            for chunk_id in relevant_chunk_ids:
                print(f"  ✅ {chunk_id}")

        else:

            print("  ⚠️ None")

        # -----------------------------------------
        # Save after EVERY question
        # -----------------------------------------

        OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                gold_dataset,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"\nSaved progress to: {OUTPUT_FILE}"
        )

    print("\n" + "=" * 100)
    print("GROUND TRUTH LABELING COMPLETE")
    print("=" * 100)

    print(
        f"Total processed: {len(gold_dataset)}"
    )

    labeled = sum(
        bool(
            item["relevant_chunk_ids"]
        )
        for item in gold_dataset
    )

    print(
        f"Questions with labels: {labeled}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()