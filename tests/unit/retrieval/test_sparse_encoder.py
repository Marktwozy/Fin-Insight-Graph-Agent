from fin_insight_graph_agent.retrieval.sparse_encoder import SimpleSparseEncoder


def test_sparse_encoder_coalesces_hash_bucket_collisions():
    encoder = SimpleSparseEncoder(buckets=1)

    vector = encoder.encode("alpha beta beta")

    assert vector.indices == [0]
    assert vector.values == [3.0]