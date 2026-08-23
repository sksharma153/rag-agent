class ParentStore:
    def __init__(self):
        self.parents = {}

    def add(self, parent_chunk):
        for chunk in parent_chunk:
            self.parents[chunk.id] = chunk

    def get(self, parent_id: str):
        return self.parents[parent_id]

    def get_many(self, parent_ids: list[str]):
        return[
            self.parents[parent_id]
            for parent_id in parent_ids
            if parent_id in self.parents
        ]