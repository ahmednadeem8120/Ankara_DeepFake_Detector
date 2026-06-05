from ..config import settings


class ForensicRetriever:
    def __init__(self):
        self.collection = None

    def _init(self):
        if self.collection is not None:
            return
        import chromadb
        from chromadb.utils import embedding_functions
        client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        self.collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            embedding_function=embedding_fn,
        )

    def retrieve(self, query: str, n_results: int = None) -> list[dict]:
        self._init()
        n = n_results or settings.RAG_TOP_K
        results = self.collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        retrieved = []
        for i in range(len(results["ids"][0])):
            retrieved.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "source": results["metadatas"][0][i].get("title", results["metadatas"][0][i].get("source", "unknown")),
                "relevance_score": 1.0 - results["distances"][0][i],
            })
        return retrieved

    def retrieve_for_detection(self, detection_result: dict) -> list[dict]:
        evidence = detection_result.get("evidence", [])
        artifact_types = {ev.get("artifact_type", "") for ev in evidence}

        type_to_query = {
            "texture_anomaly": "spatial texture artifacts deepfake detection DINOv2 vision transformer",
        }

        queries = [type_to_query[t] for t in artifact_types if t in type_to_query]
        if not queries:
            queries = ["deepfake detection forensic analysis techniques"]

        all_results = []
        seen_ids = set()
        for q in queries[:3]:
            for r in self.retrieve(q, n_results=3):
                doc_id = r["metadata"].get("file_hash", "") + str(r["metadata"].get("chunk_index", 0))
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append(r)

        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return all_results[:settings.RAG_TOP_K]
