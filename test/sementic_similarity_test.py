from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

sentences = [
    "I forgot my password",
    "I cannot login",
    "My account is locked",
    "How to cook pasta"
]

embeddings = model.encode(
    sentences,
    normalize_embeddings=True
)

print(cos_sim(embeddings[0], embeddings[1]))
print(cos_sim(embeddings[0], embeddings[2]))
print(cos_sim(embeddings[0], embeddings[3]))