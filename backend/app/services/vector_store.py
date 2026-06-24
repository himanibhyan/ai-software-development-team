from __future__ import annotations

import asyncio
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Service for interacting with ChromaDB vector store.

    Handles embedding generation, document storage, and similarity search
    for project artifacts, code templates, and agent memory.
    """

    def __init__(self) -> None:
        self._client: chromadb.Client | None = None
        self._embedding_fn: embedding_functions.OpenAIEmbeddingFunction | None = None

    async def initialize(self) -> None:
        """Initialize ChromaDB client and embedding function."""
        try:
            self._client = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chromadb.HttpClient(
                        host=settings.CHROMA_HOST,
                        port=settings.CHROMA_PORT,
                        settings=ChromaSettings(
                            anonymized_telemetry=False,
                        ),
                    ),
                ),
                timeout=3.0,
            )

            self._embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_EMBEDDING_MODEL,
            )

            # Ensure collections exist
            self._get_or_create_collection(settings.CHROMA_COLLECTION_PROJECTS)
            self._get_or_create_collection(settings.CHROMA_COLLECTION_TEMPLATES)
            self._get_or_create_collection(settings.CHROMA_COLLECTION_MEMORY)

            logger.info("chromadb_initialized", host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        except Exception as e:
            logger.warning("chromadb_initialization_failed", error=str(e))
            self._client = None

    def _get_or_create_collection(self, name: str) -> Any:
        if self._client is None:
            raise RuntimeError("ChromaDB client not initialized")
        try:
            return self._client.get_collection(name)
        except ValueError:
            return self._client.create_collection(
                name=name,
                embedding_function=self._embedding_fn,
            )

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def store_artifact(
        self,
        collection_name: str,
        document_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Store an artifact chunk in the vector store."""
        if not self._client:
            logger.warning("chromadb_not_available", operation="store")
            return False

        try:
            collection = self._get_or_create_collection(collection_name)
            collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[document_id],
            )
            return True
        except Exception as e:
            logger.error("chromadb_store_failed", error=str(e), document_id=document_id)
            return False

    async def search_similar(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents in the vector store."""
        if not self._client:
            logger.warning("chromadb_not_available", operation="search")
            return []

        try:
            collection = self._get_or_create_collection(collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata,
            )

            documents = []
            for i in range(len(results["ids"][0])):
                documents.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                )
            return documents
        except Exception as e:
            logger.error("chromadb_search_failed", error=str(e))
            return []

    async def delete_artifact(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the vector store."""
        if not self._client:
            return False
        try:
            collection = self._get_or_create_collection(collection_name)
            collection.delete(ids=[document_id])
            return True
        except Exception as e:
            logger.error("chromadb_delete_failed", error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check if ChromaDB is reachable."""
        if not self._client:
            return False
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False


vector_store = VectorStoreService()
