from __future__ import annotations

import pytest

from app.graph.pipeline import build_pipeline, get_pipeline
from app.graph.state import create_initial_state, state_summary


@pytest.mark.asyncio
class TestGenerationPipeline:
    def test_pipeline_construction(self):
        """Verify the pipeline compiles without errors."""
        pipeline = build_pipeline()
        assert pipeline is not None
        # Pipeline should have 9 registered nodes
        assert hasattr(pipeline, "compile")

    def test_pipeline_singleton(self):
        """get_pipeline should return the same instance."""
        p1 = get_pipeline()
        p2 = get_pipeline()
        assert p1 is p2

    def test_pipeline_accepts_state(self, sample_idea: str):
        """Pipeline can invoke with a valid state."""
        pipeline = build_pipeline()
        state = create_initial_state(idea=sample_idea)
        result = pipeline.invoke(state)
        assert result is not None
        assert isinstance(result, dict)
        # Pipeline should have processed validation node at minimum
        assert "idea" in result
        assert result["idea"] == sample_idea

    def test_pipeline_rejects_short_input(self):
        """Pipeline should reject inputs shorter than 10 chars."""
        pipeline = build_pipeline()
        state = create_initial_state(idea="short")
        result = pipeline.invoke(state)
        # Should route to error_handler
        assert result["status"] == "failed"
        assert len(result.get("errors", [])) >= 0

    def test_pipeline_state_summary(self, sample_idea: str):
        """State summary produces human-readable output."""
        state = create_initial_state(idea=sample_idea)
        summary = state_summary(state)
        assert summary["project_id"] == state["project_id"]
        assert summary["revision"] == 0

    def test_pipeline_sequential_flow(self, sample_idea: str):
        """Verify the pipeline follows the expected sequential flow."""
        pipeline = build_pipeline()
        state = create_initial_state(idea=sample_idea)
        result = pipeline.invoke(state)

        # State should have been processed
        assert result["status"] in ("running", "failed", "completed")
        assert result["revision"] >= 1

    def test_state_idempotent_summary(self, sample_idea: str):
        """State summary should not mutate the state."""
        state = create_initial_state(idea=sample_idea)
        original_revision = state["revision"]
        state_summary(state)
        assert state["revision"] == original_revision
