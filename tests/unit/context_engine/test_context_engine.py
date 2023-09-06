import pytest
from unittest.mock import create_autospec

from context_engine.context_engine import ContextEngine
from context_engine.context_engine.context_builder.base import BaseContextBuilder
from context_engine.knoweldge_base.base import BaseKnowledgeBase
from context_engine.knoweldge_base.models import QueryResult, DocumentWithScore
from context_engine.models.data_models import Query, Context, ContextContent


class TestContextEngine:

    @staticmethod
    @pytest.fixture
    def mock_knowledge_base():
        return create_autospec(BaseKnowledgeBase)

    @staticmethod
    @pytest.fixture
    def mock_context_builder():
        return create_autospec(BaseContextBuilder)

    @staticmethod
    @pytest.fixture
    def context_engine(mock_knowledge_base, mock_context_builder):
        return ContextEngine(mock_knowledge_base, mock_context_builder)

    @staticmethod
    @pytest.fixture
    def sample_context_text():
        return (
            "Photosynthesis is the process used by plants, algae and certain bacteria "
            "to harness energy from sunlight and turn it into chemical energy."
        )

    @staticmethod
    @pytest.fixture
    def mock_global_metadata_filter():
        return {"source": "Wikipedia"}

    @staticmethod
    @pytest.fixture
    def mock_query_result(sample_context_text):
        return [
            QueryResult(
                query="How does photosynthesis work?",
                documents=[
                    DocumentWithScore(
                        id="1",
                        text=sample_context_text,
                        metadata={"source": "Wikipedia"},
                        score=0.95
                    )
                ]
            )
        ]

    @staticmethod
    def test_query(context_engine,
                   mock_knowledge_base,
                   mock_context_builder,
                   sample_context_text,
                   mock_query_result):
        queries = [Query(text="How does photosynthesis work?")]
        max_context_tokens = 100

        mock_context_content = create_autospec(ContextContent)
        mock_context_content.to_text.return_value = sample_context_text
        mock_context = Context(content=mock_context_content, num_tokens=21)

        mock_knowledge_base.query.return_value = mock_query_result
        mock_context_builder.build.return_value = mock_context

        result = context_engine.query(queries, max_context_tokens)

        assert result == mock_context
        mock_knowledge_base.query.assert_called_once_with(
            queries, global_metadata_filter=None)
        mock_context_builder.build.assert_called_once_with(
            mock_query_result, max_context_tokens)

    @staticmethod
    def test_query_with_metadata_filter(context_engine,
                                        mock_knowledge_base,
                                        mock_context_builder,
                                        sample_context_text,
                                        mock_query_result,
                                        mock_global_metadata_filter):
        queries = [Query(text="How does photosynthesis work?")]
        max_context_tokens = 100

        mock_context_content = create_autospec(ContextContent)
        mock_context_content.to_text.return_value = sample_context_text
        mock_context = Context(content=mock_context_content, num_tokens=21)

        mock_knowledge_base.query.return_value = mock_query_result
        mock_context_builder.build.return_value = mock_context

        context_engine_with_filter = ContextEngine(
            mock_knowledge_base,
            mock_context_builder,
            global_metadata_filter=mock_global_metadata_filter
        )

        result = context_engine_with_filter.query(queries, max_context_tokens)

        assert result == mock_context
        mock_knowledge_base.query.assert_called_once_with(
            queries, global_metadata_filter=mock_global_metadata_filter)
        mock_context_builder.build.assert_called_once_with(
            mock_query_result, max_context_tokens)

    @staticmethod
    def test_multiple_queries(context_engine,
                              mock_knowledge_base,
                              mock_context_builder,
                              sample_context_text,
                              mock_query_result):
        queries = [
            Query(text="How does photosynthesis work?"),
            Query(text="What is cellular respiration?")
        ]
        max_context_tokens = 200

        text = (
            "Cellular respiration is a set of metabolic reactions and processes "
            "that take place in the cells of organisms to convert biochemical energy "
            "from nutrients into adenosine triphosphate (ATP)."
        )

        extended_mock_query_result = mock_query_result + [
            QueryResult(
                query="What is cellular respiration?",
                documents=[
                    DocumentWithScore(
                        id="2",
                        text=text,
                        metadata={"source": "Wikipedia"},
                        score=0.93
                    )
                ]
            )
        ]

        mock_knowledge_base.query.return_value = extended_mock_query_result

        combined_text = sample_context_text + "\n" + text
        mock_context_content = create_autospec(ContextContent)
        mock_context_content.to_text.return_value = combined_text
        mock_context = Context(content=mock_context_content, num_tokens=40)

        mock_context_builder.build.return_value = mock_context

        result = context_engine.query(queries, max_context_tokens)

        assert result == mock_context

    @staticmethod
    def test_empty_query_results(context_engine,
                                 mock_knowledge_base,
                                 mock_context_builder):
        queries = [Query(text="Unknown topic")]
        max_context_tokens = 100

        mock_knowledge_base.query.return_value = []

        mock_context_content = create_autospec(ContextContent)
        mock_context_content.to_text.return_value = ""
        mock_context = Context(content=mock_context_content, num_tokens=0)

        mock_context_builder.build.return_value = mock_context

        result = context_engine.query(queries, max_context_tokens)

        assert result == mock_context

    @staticmethod
    @pytest.mark.asyncio
    async def test_aquery_not_implemented(context_engine):
        queries = [Query(text="What is quantum physics?")]
        max_context_tokens = 10

        with pytest.raises(NotImplementedError):
            await context_engine.aquery(queries, max_context_tokens)