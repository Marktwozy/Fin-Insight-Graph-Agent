from pathlib import Path


def test_compose_declares_required_services():
    compose_text = Path("D:/myAgent/.worktrees/fin-insight-v1/docker-compose.yml").read_text(encoding="utf-8")
    for service_name in ["postgres", "qdrant", "neo4j", "prometheus", "grafana"]:
        assert service_name in compose_text