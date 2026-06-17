from config import Configuration
from services.planner import PlanningService


def test_extract_tasks_from_object_payload():
    service = PlanningService(planner_agent=None, config=Configuration())  # type: ignore[arg-type]

    tasks = service._extract_tasks(
        '{"tasks":[{"title":"Background","intent":"Understand context","query":"topic background"}]}'
    )

    assert tasks == [
        {
            "title": "Background",
            "intent": "Understand context",
            "query": "topic background",
        }
    ]


def test_extract_tasks_from_array_payload():
    service = PlanningService(planner_agent=None, config=Configuration())  # type: ignore[arg-type]

    tasks = service._extract_tasks(
        '[{"title":"Market","intent":"Find market data","query":"market data"}]'
    )

    assert tasks[0]["title"] == "Market"


def test_extract_tasks_returns_empty_for_invalid_payload():
    service = PlanningService(planner_agent=None, config=Configuration())  # type: ignore[arg-type]

    assert service._extract_tasks("not json") == []
