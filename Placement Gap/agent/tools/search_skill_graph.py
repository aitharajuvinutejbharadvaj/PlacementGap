from ontology.graph import ancestors


def search_skill_graph(
    node_id: str, depth: int = 2, edge_types: list[str] | None = None
) -> list[str]:
    return sorted(ancestors(node_id))[: max(0, depth * 20)]
