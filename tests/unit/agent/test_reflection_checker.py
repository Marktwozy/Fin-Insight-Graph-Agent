from fin_insight_graph_agent.agent.nodes.reflection_checker import ReflectionChecker


def test_reflection_flags_unsupported_claims():
    checker = ReflectionChecker()
    report = checker.check(
        draft_text="This definitely proves every NVIDIA supplier will be disrupted.",
        evidence_texts=["NVIDIA disclosed supply constraints at advanced packaging partners."],
    )
    assert report.requires_revision is True
    assert report.unsupported_claims