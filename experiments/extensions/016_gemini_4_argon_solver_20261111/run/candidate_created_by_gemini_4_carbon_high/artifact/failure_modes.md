# HolonomyWeave Failure Modes Analysis

**HolonomyWeave** is engineered so that common heuristic shortcuts, algebraic misconceptions, and shallow graph-search approximations produce systematically wrong integer answers on specific holonomy queries. Every item packs three distinct holonomy-sector optima $d^*(q_0), d^*(q_1), d^*(q_2)$ into $d^*(q_0)\cdot 10^8 + d^*(q_1)\cdot 10^4 + d^*(q_2)$, requiring simultaneous exactness across all three queried fiber states.

## 1. Base-Graph Greedy / Holonomy-Blind Shortest Path

- **Mechanism**: Computing the shortest directed path from `source` to `sink` on the base graph $G = (V, E)$ without lifting to $V \times D_M$.
- **Why it fails**: In every generated instance (`hw_001` through `hw_030`), the minimum-cost base trunk path arrives at `sink` in the identity holonomy state $(+1, 0)$, whereas none of the queried triples $[q_0, q_1, q_2]$ asks for $(+1, 0)$ across all slots. Furthermore, Johnson scalar potentials $\phi(u) - \phi(v)$ distort individual edge weights by up to $\pm 15$ while preserving path sums, defeating greedy next-hop edge selection.

## 2. Simple-Path / Acyclic Walk Assumption

- **Mechanism**: Restricting search to simple paths in $V$ (visiting each base vertex at most once) rather than simple paths in the lifted bundle $V \times D_M$.
- **Why it fails**: In Tier 1 (`M = 7`, query $[+1, 6]$), Tier 2 (counter-winding queries $[+1, 5], [+1, 6], [+1, M-1], [+1, M-2]$), and Tier 3 (double-reflection queries $[+1, 5], [+1, M-1]$), the unique global optimum **must** traverse a directed 2-plaquette cycle one or more times, repeating its junction vertex in $V$ with strictly distinct fiber states in $D_M$.

## 3. Monotone Non-Wrapping Modular Arithmetic (Tier 2)

- **Mechanism**: Treating modular shifts $r \in \{0, \dots, M-1\}$ as non-negative additive quantities without exploiting negative-stride wrap-around modulo $M$.
- **Why it fails**: Tier 2 weaves (`hw_007` through `hw_018`) couple a forward plaquette of shift $+1 \bmod M$ (base cost $80 \cdot \text{mult}$) with a counter-winding plaquette of shift $(M - 2) \bmod M \equiv -2 \pmod M$ (base cost $70 \cdot \text{mult}$). For $M = 9$ and query $[+1, 5]$, the forward acyclic combination costs $B_0 + 145 \cdot \text{mult}$, whereas winding **twice** around the $-2 \bmod 9$ plaquette from the zero-shift trunk achieves $(-4) \bmod 9 = 5$ at strictly lower cost $B_0 + 140 \cdot \text{mult}$ (a $5 \cdot \text{mult}$ separation).

## 4. Abelianization of $D_M$ into $\mathbb{Z}_2 \times \mathbb{Z}_M$ (Tier 3)

- **Mechanism**: Multiplying parity signs $\prod s_e$ and summing shifts $\sum r_e \bmod M$ independently instead of applying the semi-direct product rule $(s, r) \star (s_e, r_e) = (s \cdot s_e, (r + s \cdot r_e) \bmod M)$.
- **Why it fails**: In Tier 3 (`hw_019` through `hw_030`), traversing a reflection strand ($s = -1$) before a $+2$ plaquette inverts the plaquette's shift to $-2 \bmod M$. An abelianized solver predicts $+2 \bmod M$ regardless of parity history and misses every reflection-conjugated optimum.

## 5. Symmetry-Conserving Sheet Restriction on $s_{\text{query}} = +1$ (Tier 3)

- **Mechanism**: Assuming that because a queried target state $[+1, r_q]$ has orientation parity $+1$, an optimal walk remains in the $s = +1$ sheet throughout.
- **Why it fails**: For Tier 3 queries $[+1, 5]$ (when $M = 7$, $r_q = M - 2 = 5$, and when $M = 9$, $r_q = 5$) and $[+1, M - 1]$, the unique minimum-cost walk **breaks orientation symmetry** at Stage 1 into the $s = -1$ sheet, winds around the post-stage $+2$ plaquette while inverted (effectively stepping by $-2 \bmod M$), and reflects a **second time** before `sink` to restore $s = +1$. Restricting to $s = +1$ overestimates $d^*(+1, 5)$ by $80 \cdot \text{mult}$ on $M = 7$ and by $10 \cdot \text{mult}$ on $M = 9$.

## 6. Left-Action vs. Right-Action Composition Reversal (Tier 3)

- **Mechanism**: Updating state via $(s_e, r_e) \star (s, r) = (s_e \cdot s, (r_e + s_e \cdot r) \bmod M)$ instead of right-multiplication $(s, r) \star (s_e, r_e)$.
- **Why it fails**: Because vertex gauge transformations $\gamma(u) \tilde{g}_e \gamma(v)^{-1}$ assign $g_s[v] = -1$ to half of the internal vertices in Tier 3, reversing multiplication order destroys telescoping cancellation of $\gamma(v)^{-1}\gamma(v)$ at internal vertices and corrupts the holonomy of every multi-edge walk.

## 7. Signed Remainder Bug on Negative Shifts

- **Mechanism**: Using C/JavaScript truncated remainder `%` (which can yield negative values in $[-(M-1), -1]$ when $s = -1$ and $r + s \cdot r_e < 0$) instead of the canonical mathematical residue in $\{0, \dots, M-1\}$.
- **Why it fails**: Negative remainders split single fiber states in $D_M$ into spurious negative keys and prevent state-space merges or target state matching at `(sink, sq, rq)`.
