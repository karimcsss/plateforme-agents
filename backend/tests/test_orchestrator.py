import pytest
from app.orchestrator.dag_runner import _topological_batches
from app.models.plan import RequiredAgent


def test_parallel_agents_same_batch():
    agents = [
        RequiredAgent(id="a", role="r", goal="g", tools=["web_search"], depends_on=[]),
        RequiredAgent(id="b", role="r", goal="g", tools=["web_search"], depends_on=[]),
    ]
    batches = _topological_batches(agents)
    assert len(batches) == 1
    assert len(batches[0]) == 2


def test_dependent_agents_separate_batches():
    agents = [
        RequiredAgent(id="a", role="r", goal="g", tools=["web_search"], depends_on=[]),
        RequiredAgent(id="b", role="r", goal="g", tools=["web_search"], depends_on=["a"]),
    ]
    batches = _topological_batches(agents)
    assert len(batches) == 2
    assert batches[0][0].id == "a"
    assert batches[1][0].id == "b"


def test_diamond_shape_dag():
    """a -> b, a -> c, [b,c] -> d : 3 vagues, b et c en parallèle."""
    agents = [
        RequiredAgent(id="a", role="r", goal="g", tools=["web_search"], depends_on=[]),
        RequiredAgent(id="b", role="r", goal="g", tools=["web_search"], depends_on=["a"]),
        RequiredAgent(id="c", role="r", goal="g", tools=["web_search"], depends_on=["a"]),
        RequiredAgent(id="d", role="r", goal="g", tools=["web_search"], depends_on=["b", "c"]),
    ]
    batches = _topological_batches(agents)
    assert len(batches) == 3
    assert len(batches[1]) == 2  # b et c ensemble