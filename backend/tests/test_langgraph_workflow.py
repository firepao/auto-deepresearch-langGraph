from graph.workflow import LangGraphWorkflow, LangGraphWorkflowUnavailable


def test_langgraph_workflow_scaffold_invokes_when_dependency_available():
    try:
        workflow = LangGraphWorkflow()
    except LangGraphWorkflowUnavailable:
        return

    state = workflow.invoke("test topic")

    assert state["status"] == "langgraph_scaffold_ready"
    assert "test topic" in state["report_markdown"]
