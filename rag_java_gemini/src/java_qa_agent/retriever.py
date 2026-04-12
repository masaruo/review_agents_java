from pathlib import Path
from typing import List

import chromadb

from .schemas.models import JavaChunk, JavaChunkMetadata


class Retriever:
    def __init__(self, index_dir: str, project_name: str):
        self.index_path = Path(index_dir).expanduser() / project_name
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.index_path))
        self.collection = self.client.get_or_create_collection(name="java_code")

    def add_chunks(
        self, chunks: List[JavaChunk], embeddings: List[List[float]]
    ) -> None:
        documents = [c.content for c in chunks]
        metadatas = [c.metadata.model_dump() for c in chunks]
        ids = [f"{c.metadata.file_path}_{i}" for i, c in enumerate(chunks)]

        self.collection.add(
            documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
        )

    def query(self, embedding: List[float], top_k: int = 5) -> List[JavaChunk]:
        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)

        chunks = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                chunks.append(
                    JavaChunk(
                        content=results["documents"][0][i],
                        metadata=JavaChunkMetadata.model_validate(
                            results["metadatas"][0][i]
                        ),
                    )
                )
        return chunks

    def delete_index(self) -> None:
        self.client.delete_collection("java_code")
        # Re-create empty collection
        self.collection = self.client.get_or_create_collection(name="java_code")
