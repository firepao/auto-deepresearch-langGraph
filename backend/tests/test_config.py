from config import Configuration, SearchAPI


def test_configuration_from_env_parses_langgraph_flag(monkeypatch):
    monkeypatch.setenv("USE_LANGGRAPH_WORKFLOW", "true")
    monkeypatch.setenv("SEARCH_API", "duckduckgo")

    config = Configuration.from_env()

    assert config.use_langgraph_workflow is True
    assert config.search_api is SearchAPI.DUCKDUCKGO


def test_configuration_overrides_take_precedence(monkeypatch):
    monkeypatch.setenv("SEARCH_API", "duckduckgo")

    config = Configuration.from_env(overrides={"search_api": "tavily"})

    assert config.search_api is SearchAPI.TAVILY
