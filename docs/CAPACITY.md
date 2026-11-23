# Capacity plan: GitGuru

Full corpus target: All reference pages, the full Pro Git book and release notes from 2.30 onwards (2,000+ pages)

<!-- generated:start -->

| Measure | Current corpus | Full corpus estimate |
|---|---:|---:|
| Pages | 966 | 2,000 |
| Tokens | 899,970 | 1,863,292 |
| Tokens per page | 932 | 932 |
| Chunks (500 tokens) | 1,800 | 3,727 |
| Embedding cost | — | Rs 35.40 |
| Vector storage | — | 14.56 MB |
| Text storage | 6.64 MB | 13.75 MB |

<!-- generated:end -->

## What I conclude

1. Embedding cost is estimated at Rs 35.40 for 1,863,292 tokens; this is a one-time estimate.
2. Compare the estimated text and vector storage above with the storage limit shown on your database dashboard.
3. The least certain number is tokens per page; measure it again after collecting a larger and more varied sample.
4. At 10 times the corpus size, tokens, chunks, embedding cost and storage will be approximately 10 times larger. Recheck database capacity and embedding budget before expanding.
