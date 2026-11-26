# arXiv:2406.11717 §4.1 — verbatim extract

Source: https://arxiv.org/html/2406.11717v3, §4.1 "Weight orthogonalization", fetched
2026-11-24 with `firecrawl scrape`. The full page copy was not retained; this is the passage the
method document relies on.

> Specifically, we can take each matrix $W_{out} \in \mathbb{R}^{d_{model} \times d_{input}}$ that
> writes to the residual stream, and orthogonalize its column vectors with respect to $\hat{\mathbf r}$:
> $W_{out}' \leftarrow W_{out} - \hat{\mathbf r}\hat{\mathbf r}^{\intercal} W_{out}$. (5)
>
> In a transformer architecture, the matrices that write to the residual stream are: the embedding
> matrix, the positional embedding matrix, attention out matrices, and MLP out matrices.
> Orthogonalizing all of these matrices, as well as any output biases, with respect to the direction
> $\hat{\mathbf r}$ effectively prevents the model from ever writing $\hat{\mathbf r}$ to its residual
> stream.
>
> Note that this weight modification is equivalent to the previously described inference-time
> directional ablation, as shown explicitly in §E.

Relevance: the paper's target set is wider than this study's implementation. The method document
declares the omission of the embedding matrix, positional embeddings and output biases, and the
per-layer (rather than single global) direction, as differences rather than claiming reproduction.
