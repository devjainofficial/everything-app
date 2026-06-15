# Retrieval Concepts (sample document)

## Embeddings
An embedding is a numeric fingerprint of meaning: a model converts a piece of text
into a high-dimensional vector so that texts with similar meaning land near each other
in vector space. The same embedding model must be used for both stored documents and
incoming queries, otherwise their vectors live in different spaces and cannot be compared.

## Vector (semantic) search
Vector search retrieves the stored chunks whose embeddings are nearest to the query's
embedding, typically measured by cosine distance. It captures meaning and paraphrase, so
a query about "a fast way to look up nearest neighbours" can match a passage on approximate
nearest neighbour indexes even when no keywords are shared.

## Keyword search and BM25
Keyword search ranks documents by exact term overlap using statistics like term frequency
and inverse document frequency. BM25 is the classic scoring function. Keyword search excels
at rare, exact tokens — names, error codes, and technical jargon such as "RRF" or "BM25"
itself — where embeddings sometimes drift.

## Hybrid search and Reciprocal Rank Fusion (RRF)
Hybrid search combines keyword and vector results to capture the strengths of both.
Reciprocal Rank Fusion (RRF) merges two ranked lists by scoring each item as the sum of
1 / (k + rank) across the lists, rewarding items that rank highly in either list without
requiring the two scoring systems to be on the same scale.

## Cross-encoder reranking
A retriever returns a shortlist quickly; a cross-encoder reranker then reads each
query-and-chunk pair together and scores relevance more precisely. Running a reranker over
the shortlist — not the whole corpus — sharpens the final ordering at modest extra cost.
