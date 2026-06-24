from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.vector_store import VectorStoreService


@pytest.fixture
def vs() -> VectorStoreService:
    return VectorStoreService()


@pytest.fixture
def mock_chroma_client():
    client = MagicMock()
    client.get_collection = MagicMock()
    client.create_collection = MagicMock()
    client.heartbeat = MagicMock()
    return client


class TestInitialize:
    async def test_success(self, vs, mock_chroma_client):
        with (
            patch("app.services.vector_store.chromadb.HttpClient", return_value=mock_chroma_client),
            patch("app.services.vector_store.embedding_functions.OpenAIEmbeddingFunction"),
            patch("app.services.vector_store.settings.CHROMA_COLLECTION_PROJECTS", "projects"),
            patch("app.services.vector_store.settings.CHROMA_COLLECTION_TEMPLATES", "templates"),
            patch("app.services.vector_store.settings.CHROMA_COLLECTION_MEMORY", "memory"),
        ):
            await vs.initialize()

        assert vs._client is not None
        assert vs._embedding_fn is not None
        assert mock_chroma_client.get_collection.call_count == 3

    async def test_failure_sets_client_to_none(self, vs):
        with patch("app.services.vector_store.chromadb.HttpClient", side_effect=Exception("conn refused")):
            await vs.initialize()

        assert vs._client is None


class TestIsAvailable:
    def test_returns_true_when_client_set(self, vs):
        vs._client = MagicMock()
        assert vs.is_available is True

    def test_returns_false_when_client_none(self, vs):
        vs._client = None
        assert vs.is_available is False


class TestStoreArtifact:
    async def test_stores_successfully(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        collection = MagicMock()
        mock_chroma_client.get_collection.return_value = collection

        result = await vs.store_artifact("test_collection", "doc_1", "some text", {"key": "val"})

        assert result is True
        collection.add.assert_called_once_with(
            documents=["some text"],
            metadatas=[{"key": "val"}],
            ids=["doc_1"],
        )

    async def test_returns_false_when_no_client(self, vs):
        vs._client = None
        result = await vs.store_artifact("col", "id", "text")
        assert result is False

    async def test_returns_false_on_exception(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        mock_chroma_client.get_collection.side_effect = Exception("fail")

        result = await vs.store_artifact("col", "id", "text")
        assert result is False


class TestSearchSimilar:
    async def test_returns_documents(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        collection = MagicMock()
        collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["text1", "text2"]],
            "metadatas": [[{"k": "v1"}, {"k": "v2"}]],
            "distances": [[0.1, 0.2]],
        }
        mock_chroma_client.get_collection.return_value = collection

        results = await vs.search_similar("col", "query", n_results=2)

        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["text"] == "text1"
        assert results[0]["distance"] == 0.1

    async def test_returns_empty_when_no_client(self, vs):
        vs._client = None
        results = await vs.search_similar("col", "query")
        assert results == []

    async def test_returns_empty_on_exception(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        mock_chroma_client.get_collection.side_effect = Exception("fail")

        results = await vs.search_similar("col", "query")
        assert results == []

    async def test_with_filter_metadata(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        collection = MagicMock()
        collection.query.return_value = {
            "ids": [["id1"]],
            "documents": [["text1"]],
            "metadatas": [[{"type": "test"}]],
            "distances": [[0.5]],
        }
        mock_chroma_client.get_collection.return_value = collection

        results = await vs.search_similar("col", "query", filter_metadata={"type": "test"})

        collection.query.assert_called_once_with(
            query_texts=["query"],
            n_results=5,
            where={"type": "test"},
        )
        assert len(results) == 1

    async def test_handles_none_metadatas_and_distances(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        collection = MagicMock()
        collection.query.return_value = {
            "ids": [["id1"]],
            "documents": [["text1"]],
            "metadatas": None,
            "distances": None,
        }
        mock_chroma_client.get_collection.return_value = collection

        results = await vs.search_similar("col", "query")
        assert results[0]["metadata"] == {}
        assert results[0]["distance"] == 0.0


class TestDeleteArtifact:
    async def test_deletes_successfully(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        collection = MagicMock()
        mock_chroma_client.get_collection.return_value = collection

        result = await vs.delete_artifact("col", "doc_1")
        assert result is True
        collection.delete.assert_called_once_with(ids=["doc_1"])

    async def test_returns_false_when_no_client(self, vs):
        vs._client = None
        result = await vs.delete_artifact("col", "id")
        assert result is False

    async def test_returns_false_on_exception(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        mock_chroma_client.get_collection.side_effect = Exception("fail")

        result = await vs.delete_artifact("col", "id")
        assert result is False


class TestHealthCheck:
    async def test_returns_true_when_heartbeat_succeeds(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client

        result = await vs.health_check()
        assert result is True
        mock_chroma_client.heartbeat.assert_called_once()

    async def test_returns_false_when_no_client(self, vs):
        vs._client = None
        result = await vs.health_check()
        assert result is False

    async def test_returns_false_on_exception(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        mock_chroma_client.heartbeat.side_effect = Exception("down")

        result = await vs.health_check()
        assert result is False


class TestGetOrCreateCollection:
    async def test_gets_existing_collection(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        existing = MagicMock()
        mock_chroma_client.get_collection.return_value = existing

        result = vs._get_or_create_collection("my_col")
        assert result == existing
        mock_chroma_client.create_collection.assert_not_called()

    async def test_creates_new_collection(self, vs, mock_chroma_client):
        vs._client = mock_chroma_client
        vs._embedding_fn = MagicMock()
        mock_chroma_client.get_collection.side_effect = ValueError("not found")
        new_col = MagicMock()
        mock_chroma_client.create_collection.return_value = new_col

        result = vs._get_or_create_collection("new_col")
        assert result == new_col
        mock_chroma_client.create_collection.assert_called_once_with(
            name="new_col",
            embedding_function=vs._embedding_fn,
        )

    async def test_raises_when_client_none(self, vs):
        vs._client = None
        with pytest.raises(RuntimeError, match="not initialized"):
            vs._get_or_create_collection("col")
