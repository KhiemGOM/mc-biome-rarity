# Theory: the mathematical model, its estimators, and why the code computes them

This document is split in three on purpose.

1. **The model** (sections 1 and 2): random variables and the estimand, with no reference to code.
2. **The estimators** (section 3): what converges to what, how fast, and when the confidence interval is valid.
3. **The code** (section 4): a step by step argument that the programs compute the model's estimator, with every gap named and bounded.
4. **The certified sampler** (section 6): `certrun.py`, which enforces every hypothesis of a finite N simultaneous guarantee.

Every claim carries one tag.

| tag | meaning |
|---|---|
| **[P]** | proven here from the definitions alone |
| **[P \| A1, ...]** | proven here, conditional on the listed assumptions |
| **[A]** | an assumption. Stated, used, not provable from the code |
| **[E]** | an estimate from data, with the uncertainty it carries |
| **[C]** | a fact about the code, checked by reading it and by the named test |

Numerical checks of the theorems on synthetic worlds with known truth are in `tests/test_theory.py` (pure numpy, no Cubiomes, 16 tests), and the reference implementations they use are in `theory.py`.

## 0. Every constant and every interpretation step (audit, 2026-11-22)

**Why this section exists.** The earlier certificate said "under A1 and A2" while the sentence we quoted ("mean walk to find the biome") also needed H (section 1.4) and ignored the first 4,000 blocks. The interval was valid for the quantity it covered ($M$, the inverse hazard on the 4,000 to 20,000 window); the *label* needed two more steps that were not on the certificate. From now on every step from data to a quoted sentence is a row below, and the certificate lists all of them.

### 0.1 Interpretation steps (data to sentence)

| step | from | to | status |
|---|---|---|---|
| I1 | the seeds we ran | iid uniform seeds | [A] A1 (tested by fold chi-square) |
| I2 | the 4 angles of a seed | each angle uniform and independent of the map | [P] by construction, A2 |
| I3 | the code's distances | the model's $D$ | [P] + [C] sections 4 and 6.3, rounding $\le \frac12$ block |
| I4 | $\mathbb E[\min(D, C)]$ | a lower bound on $\mathbb E[D]$ from spawn | [P] Theorem 18, no assumption |
| I5 | the far half $[C/2, C]$ of each ray | the mean tail past the cap $C$ | [A] $H_C$ (constant hazard from $C/2$ on). Affects only the tail share, planned $< 5\%$ |
| I6 | the model | the game (spawn search, surface layer, no terrain, no line of sight) | [A] modelling, section 4.1 item 6, not provable here |
| I7 (old) | $M$ on $[4000, 20000]$ | "mean walk" | needed H *and* ignored the spawn start. Retired as a headline; kept as the far-field rate |

### 0.2 Constants

"Estimand" says whether changing the value changes the number being estimated (yes) or only the cost and width (no).

| constant | value | where | why it exists | estimand? | chosen by | decide? |
|---|---|---|---|---|---|---|
| game version | 1.21 | all C code | the study is about 1.21 | yes | you | no |
| start point | `estimateSpawn` | discexact | "walk from spawn" | yes | you (spawn included, 2026-11-22) | no |
| biome layer | every layer of the 4x4 column, y = -64..319 (`--layers all`, section 8.9); was the depth 0 layer only until 2026-11-22 | discexact | a biome counts if it is anywhere in the column, caves included, as the old colsim column mode did | yes | you (caves must be in, 2026-11-22) | **yes**: whether a cave deep below counts as found, or only near the walking height |
| discovery radius $r$ | 0, 64, 128 | plan | how close counts as "found" (sight distance) | yes | placeholders (HANDOFF item 3) | **yes** |
| cap $C_r$ | from the pilot, $\approx 3\,\mathbb E[D]$ | certwalk plan | simulation must stop somewhere | **no** (Theorem 18: it splits $\mathbb E[D]$ into a certified part and a labelled tail; the sum does not depend on $C$) | Claude | no |
| tail window | $[C/2, C]$ | certwalk | where the tail rate is measured | no, only under $H_C$ | Claude | no |
| window $R_0, R$ | 4,000, 20,000 | certrun (old) | far-field rate $M$ | yes for $M$; not used by the new headline | Claude | retired |
| rays per seed $J$ | 4 | plan | cost sharing (one spawn search, one generator per seed) | no (every ray has the same law) | Claude | no |
| angle offset $U$ | splitmix of the seed | discexact | random orientation | no | Claude | no |
| stride $k$ | 1 (exact) | certrun / certwalk | older runs used sparse grids | yes for $k > 1$ (Theorem 2); certified runs use $k = 1$ only | Claude | no |
| uniform start box $L$ | $10^6$ blocks | certwalk | the "random start" baseline for the spawn bias | yes for the baseline only | Claude | **yes** (any $L$ inside the world border is a valid baseline; it fixes what "random place" means) |
| target precision | $\pm 5\%$ | plan | when to stop | no | you (earlier thread) | no |
| $\alpha$ | 0.05 total, 0.005 for non target biomes | plan | the 95% guarantee | no | Claude | no |
| tail share limit | 5% | plan | how much of $\mathbb E[D]$ may rest on $H_C$ | no (it sets $C$) | Claude | **yes** if you want less |
| target biomes | 6 rarest from the pilot | plan | where the $\alpha$ goes | no | Claude | no |
| seed ranges | fresh, ledger checked | plan | independence from the pilot (Theorem 13) | no | Claude | no |


## 1. The mathematical model

### 1.1 Population and randomness

* $\mathcal S = \{0,1\}^{64}$ is the set of world seeds. $S$ is uniform on $\mathcal S$.
* For each seed, $p(S) \in \mathbb Z^2$ is the spawn point and $\beta_S : \mathbb Z^2 \to \mathcal B$ is the surface biome of each 4x4 cell $q = (q_x, q_z)$. Both are deterministic functions of $S$ (they are *defined* as the Cubiomes functions named in section 4, so there is no approximation at this step).
* **The model has one ray.** $\Theta \sim \mathrm{Unif}[0, 2\pi)$ independent of $S$, direction $u = (\cos\Theta, \sin\Theta)$. Every estimand below is an expectation over $(S, \Theta)$: one walk from spawn in a uniformly random direction. "The mean over all directions" is the same number, since $\mathbb E[g(S,\Theta)] = \mathbb E_S\big[\frac1{2\pi}\int_0^{2\pi} g(S,\theta)\,d\theta\big]$ (Fubini).
* **The estimator uses $J$ rays per seed** (a sampler choice, not part of the model). With $U \sim \mathrm{Unif}[0,1)$ independent of $S$, ray $j$ has angle $\theta_j = 2\pi (j + U)/J$. Each $\theta_j \bmod 2\pi$ is uniform and independent of $S$.

**Proposition 0 [P] (the $J$ ray average is unbiased for the one ray model).** For any $g \ge 0$ (or integrable), $\mathbb E\big[\frac1J \sum_{j} g(S, \theta_j)\big] = \mathbb E[g(S, \Theta)]$, for every $J \ge 1$.

*Proof.* Condition on $S$ and use the independence of $U$: $\mathbb E\big[\frac1J\sum_j g(S, \theta_j)\big] = \mathbb E_S\big[\frac1J\sum_j \int_0^1 g(S, 2\pi(j+u)/J)\,du\big] = \mathbb E_S\big[\sum_j \int_{j/J}^{(j+1)/J} g(S, 2\pi v)\,dv\big] = \mathbb E_S\big[\int_0^1 g(S, 2\pi v)\,dv\big] = \mathbb E[g(S,\Theta)]$, with the substitution $v = (j + u)/J$ on each term. $\square$

**Correction (2026-11-22).** Earlier versions said each $\theta_j$ is marginally uniform on $[0, 2\pi)$. That is false: $\theta_j$ is uniform on the sector $[2\pi j/J, 2\pi (j+1)/J)$. Nothing proven later used the per ray claim beyond what Proposition 0 gives, because every estimator sums over all $J$ rays of a seed before averaging over seeds; the statements "one ray, by identical marginals" below should be read as "by Proposition 0".

So $J$ changes only the variance and the cost per ray (one generator and one spawn search shared by $J$ rays), never the estimand. The rays of one seed are dependent (same map), which is why the seed, not the ray, is the sampling unit. In everything below, $J$ appears only in the estimators.

### 1.2 Geometry: the discovery functional

Cell $q$ is the closed square $Q_q = [4q_x - \tfrac12, 4q_x + \tfrac72] \times [4q_z - \tfrac12, 4q_z + \tfrac72]$ (the union of its 16 unit blocks). Biome $b$ occupies $P_b = \bigcup_{q : \beta_S(q) = b} Q_q$.

For a closed set $A \subset \mathbb R^2$, start point $p$, unit direction $u$ and discovery radius $r \ge 0$:

$$
D(A, r) = \begin{cases} \operatorname{dist}(p, A) & \text{if } \operatorname{dist}(p, A) \le r \\ \inf\{ s \ge 0 : \operatorname{dist}(p + s u, A) \le r \} + r & \text{otherwise} \end{cases}
\qquad (\inf \emptyset = \infty).
$$

In words: if the biome is already within $r$ of spawn, walk straight to it; otherwise walk the ray until it is within $r$, then walk the remaining $r$ to it. $r = 0$ is the centerline model.

* **Exact model:** $D_{b,r} = D(P_b, r)$.
* **Sparse model, stride $k$:** only cells with $k \mid q_x$ and $k \mid q_z$ are looked at. $S_k(b) = \bigcup \{ Q_q : \beta_S(q) = b,\ k \mid q_x,\ k \mid q_z \}$ and $D^k_{b,r} = D(S_k(b), r)$. $k = 4$ is the 16 block lattice.

### 1.3 Window variables and the estimand

Fix $R_0 = 4000$, $R = 20000$. For one ray with first-discovery distance $d$:

$$ x(d) = \big(\min(d, R) - R_0\big)\,\mathbf 1\{d \ge R_0\}, \qquad e(d) = \mathbf 1\{R_0 \le d \le R\}. $$

Per seed, $X = \sum_{j} x(D^{(j)})$ and $E = \sum_j e(D^{(j)})$. The estimand for biome $b$ and radius $r$ is

$$ M = \frac{\mathbb E[X]}{\mathbb E[E]} = \frac{\mathbb E[x(D)]}{\mathbb E[e(D)]} \quad\text{(one ray of the model, by Proposition 0)}, $$

and $M_k$ is the same with $D^k$ in place of $D$.

**Assumption A3 [A]:** $\mathbb E[e(D)] > 0$ (the biome is found inside the window with positive probability). Without it $M$ is undefined.

### 1.4 What $M$ means

Let $\bar S(t) = P(D > t)$ (ties have probability 0 here or are irrelevant).

**Lemma 1 [P].** $\mathbb E[x(D)] = \int_{R_0}^{R} \bar S(t)\,dt$ and $\mathbb E[e(D)] = \bar S(R_0^-) - \bar S(R)$. Hence, with $G(t) = \bar S(t)/\bar S(R_0^-)$ the survival given $D \ge R_0$,

$$ M = \frac{\int_{R_0}^{R} G(t)\,dt}{1 - G(R)} =: f(G). $$

*Proof.* $x(d) = \int_{R_0}^{R} \mathbf 1\{d > t\}\,dt$; take expectations (Tonelli). $e(D) = \mathbf 1\{D \ge R_0\} - \mathbf 1\{D > R\}$. Divide both by $\bar S(R_0^-)$. $\square$

Consequences:

* $M$ depends only on the law of $D$ given $D \ge R_0$, on the window. Whatever happens before $R_0$ (spawn biome, starting area) is removed by design.
* **[P]** If the hazard of $D$ is a constant $\lambda$ on $[R_0, R]$, then $G(t) = e^{-\lambda (t - R_0)}$ and $f(G) = \frac{(1 - e^{-\lambda L})/\lambda}{1 - e^{-\lambda L}} = 1/\lambda$ exactly ($L = R - R_0$). Test: `test_constant_hazard_gives_inverse_rate`.
* **Assumption H [A] (constant far-field hazard):** $\bar S(t) = \bar S(R_0)\,e^{-\lambda (t - R_0)}$ for all $t \ge R_0$. Under H, $M = 1/\lambda = \mathbb E[D - R_0 \mid D \ge R_0]$, the mean extra walk. **The headline numbers (144k, 114k, ...) are larger than $R$, so calling them a "mean walk" is an extrapolation that rests on H.** Without H, $M$ is still a well-defined number (the inverse occurrence/exposure rate on the window), and everything proven below about convergence to $M$ stays true; only the interpretation as a mean distance needs H. The piecewise hazard check (`certify.bin_hazards`) is the empirical test of H on the window; nothing can test it beyond $R$ without simulating beyond $R$.

**Lemma 2 [P] (monotonicity of the functional).** If $G'(t) \ge G(t)$ for all $t \in [R_0, R]$ then $f(G') \ge f(G)$.

*Proof.* The numerator of $f$ increases with $G$ pointwise; the denominator $1 - G(R)$ decreases; both are positive. $\square$ Test: `test_functional_is_monotone_in_conditional_survival`.

## 2. Properties of the estimand: sparse versus exact

### 2.1 Two facts about $D(A, r)$

**Lemma 3 [P].**
(a) $A \subseteq A' \Rightarrow D(A', r) \le D(A, r)$.
(b) For $t, r \ge 0$: $D(A, r + t) \le D(A \oplus B_t, r) + t$, where $A \oplus B_t$ is the set of points within $t$ of $A$.
(c) For $A$ a union of cells, $D(A, r) = \min_{Q_q \subseteq A} D(Q_q, r)$.

*Proof.* (a) $\operatorname{dist}(\cdot, A') \le \operatorname{dist}(\cdot, A)$, so the visibility test and the entry time can only come earlier; in the visible case $D(A', r) = \operatorname{dist}(p, A') \le \operatorname{dist}(p, A) \le D(A, r)$ because $D(A, r) \ge \operatorname{dist}(p,A)$ by the triangle inequality.
(b) $\operatorname{dist}(y, A \oplus B_t) = (\operatorname{dist}(y, A) - t)^+$, so $\operatorname{dist}(y, A\oplus B_t) \le r \iff \operatorname{dist}(y, A) \le r + t$. The two visibility tests and the two entry times $s^*$ are therefore identical. Not visible: both sides equal $s^* + r + t$. Visible: left side is $\operatorname{dist}(p, A)$, right side is $(\operatorname{dist}(p,A) - t)^+ + t \ge \operatorname{dist}(p, A)$.
(c) $\operatorname{dist}(\cdot, \cup Q) = \min \operatorname{dist}(\cdot, Q)$ and the first entry into a union of sets is the minimum of the first entries; the visible case is the same argument as in (a). $\square$

(c) is why the code can work cell by cell. It also gives the block model: the 16 blocks of a cell share one biome, their union is $Q_q$, so the cell model *equals* the block model; there is no discretisation error at this step.

### 2.2 The sign of the sparse bias

**Theorem 1 [P] (pointwise order).** If $k \mid k'$ then $S_{k'}(b) \subseteq S_k(b) \subseteq P_b$, hence $D_{b,r} \le D^k_{b,r} \le D^{k'}_{b,r}$ on every ray of every seed.

*Proof.* Multiples of $k'$ are multiples of $k$; apply Lemma 3(a). $\square$

So sparse sampling always finds a biome later or never. It is tempting to conclude $M_k \ge M$. **That does not follow:**

**Theorem 2 [P] (sign of $M_k - M$).** Write $A = \mathbb E[x(D)]$, $B = \mathbb E[e(D)]$, and $A_k, B_k$ for $D^k$.
(a) $A_k \ge A$.
(b) $M_k - M = \dfrac{(A_k - A) - M (B_k - B)}{B_k}$.
(c) $M_k - M \ge -M\, \dfrac{p_{\rm in}}{B_k}$, with $p_{\rm in} = P(D < R_0 \le D^k \le R)$.
(d) The sign is not determined by Theorem 1: there are couplings with $D^k \ge D$ everywhere and $M_k < M$.
(e) If $G_k \ge G$ on $[R_0, R]$ (the sparse first hit, given it reaches $R_0$, is stochastically later on the window), then $M_k \ge M$. In particular this holds when the hazard of $D^k$ is below that of $D$ on the window, and under H for both.

*Proof.* (a) $x$ is nondecreasing and $D^k \ge D$. (b) algebra. (c) If $e(D^k) = 1$ and $e(D) = 0$ with $D \le D^k \le R$, then $D < R_0$; so $B_k - B \le p_{\rm in}$, and with $A_k - A \ge 0$ in (b) the bound follows (if $B_k \le B$ the right side of (b) is already $\ge 0$). (d) Three rays, $D = (1000, \infty, 10000)$ and $D^k = (4001, \infty, 10000)$: $M = 22000$, $M_k = 11000.5$ (`test_pointwise_later_does_not_imply_larger_M`). (e) Lemma 2. Under H, $\bar S_k(t) \ge \bar S(t)$ for all $t$ forces $\lambda_k \le \lambda$ (let $t \to \infty$), so $M_k = 1/\lambda_k \ge 1/\lambda = M$. $\square$ Test of (c): `test_lower_bound_on_sparse_bias`.

Reading: the sparse level can only *lower* $M$ through rays whose exact hit is before $R_0$ but whose sparse hit lands inside the window (left truncation lets a new, early event in). That effect is bounded by (c) and is small when the sparse delay is small compared with $R_0$. **[E]** In the 600 seed pilot, stride 4 was above exact for all 48 biomes at all three radii; stride 2 was slightly below for 3 of 48 biome/radius pairs (minimum $-0.71\%$, within pilot noise). Theorem 2 says such negatives are allowed, so they are not evidence of a bug.

### 2.3 How big the sparse bias can be

The size of $M_k - M$ depends on the shape of the biome patches, which is a property of the Minecraft map with no closed form. What can be proven is a bound under a stated geometric condition.

**Assumption F(k, $\Delta$) [A] (covering).** $P_b \subseteq S_k(b) \oplus B_\Delta$ on the part of the map the ray explores: every point of biome $b$ is within $\Delta$ blocks of a *sampled* cell of the same biome. Equivalently $\Delta \ge h(P_b, S_k(b))$, the one-sided Hausdorff distance.

**Theorem 3 [P | F] (sandwich).** For $r \ge \Delta$, on every ray:

$$ D_{b,r} \;\le\; D^k_{b,r} \;\le\; D_{b,\,r - \Delta} + \Delta. $$

*Proof.* Left: Theorem 1. Right: $D(S_k, r) \le D(S_k \oplus B_\Delta, r - \Delta) + \Delta$ by Lemma 3(b), and $S_k \oplus B_\Delta \supseteq P_b$ by F, so Lemma 3(a) gives $\le D(P_b, r - \Delta) + \Delta$. $\square$ Test: `test_sandwich_under_covering` (k = 2 and 4, measured $\Delta$, every ray checked).

**When does F hold, and with what $\Delta$? [P]** On each axis the gap from any point to the nearest sampled cell is at most $2k - 2$ blocks (the worst point is midway between two sampled columns), so the nearest sampled cell is within $(2k-2)\sqrt2$ and lies entirely within $(2k+2)\sqrt2$. If the disc of radius $(2k+2)\sqrt 2$ around a point lies inside $P_b$, that sampled cell lies inside $P_b$ and so has biome $b$. Hence if every point of $P_b$ is within $\eta$ of such a "deep" point, F holds with $\Delta \le \eta + (2k-2)\sqrt2$. For $k = 4$: $(2k-2)\sqrt2 = 8.5$ and $(2k+2)\sqrt2 = 14.1$ blocks. On synthetic worlds of discs of radius 28 to 48 blocks the measured covering radius is $\Delta_2 = 8.9$, $\Delta_4 = 17.9$.

**F fails for any patch that contains no sampled cell** ($\Delta = \infty$), and then no bound of this kind exists: the sparse level never finds that patch (`test_sandwich_fails_without_covering`). Small patches of rare biomes are exactly this case, which is why the bias is a real effect and not a rounding issue.

**Corollary 4 [P | F, H].** If H holds for $D_r$, $D^k_r$ and $D_{r-\Delta}$, then $M_r \le M^k_r \le M_{r - \Delta}$.

*Proof.* Lower: Theorem 2(e). Upper: Theorem 3 gives $\bar S^k_r(t) \le P(D_{r-\Delta} > t - \Delta)$ for all $t$; under H both tails are exponential, so $\lambda^k_r \ge \lambda_{r-\Delta}$ (let $t \to \infty$), i.e. $M^k_r \le M_{r-\Delta}$. $\square$

**Corollary 5 [P | F, H, Steiner].** If additionally the hit rate follows the Steiner/Cauchy form $\lambda_r = \rho\,(w + 2r)$ (stationary field of patches of intensity $\rho$ and mean projected width $w$, PLAN_DISC.md), then

$$ 1 \le \frac{M^k_r}{M_r} \le \frac{w + 2r}{w + 2r - 2\Delta}. $$

So the relative bias decays like $2\Delta/(w + 2r)$: it is $O(1/r)$, it does not depend on $N$, and at $r < \Delta$ (in particular the centerline, $r = 0$) the sandwich gives nothing.

**[E] Check against the pilot (pale garden; $w$ from the pilot, $\Delta = 17.9$ taken from the synthetic fat world, not measured on Minecraft):** $w \approx 149$ from $M_0/M_{64}$ and $156$ from $M_0/M_{128}$.

| radius | bound from Corollary 5 | pilot $M^4_r/M_r - 1$ |
|---|---|---|
| 0 | none ($r < \Delta$) | +43.4% |
| 64 | +14.9% | +9.0% |
| 128 | +9.5% | +7.8% |

The pilot values sit under the bound and shrink with $r$ as predicted. This is a consistency check, not a proof that the Minecraft map satisfies F; measuring $\Delta$ per seed on the real map would turn it into one.

**Why the centerline bias is so much larger [P, Crofton].** At $r = 0$ the walker must cross a sampled 4x4 square inside the patch. Sampled squares have density $1/(4k)^2$ per block$^2$ and mean width $16/\pi$, so by the Cauchy/Crofton formula an isotropic line meets one every $\pi k^2$ blocks on average ($\approx 50$ blocks for $k = 4$). Any patch crossing much shorter than that is usually missed outright, and rare biomes are dominated by such crossings. At $r > 0$ the sampled squares are fattened by $r$ and the effect is governed by Theorem 3 instead.

## 3. The estimators and their convergence

### 3.1 Assumptions about the sampling

**A1 [A] (seeds are an iid uniform sample).** The seeds used, $S_i = \mathrm{splitmix64}(s_0 + i)$, behave as iid uniform draws from $\mathcal S$. splitmix64 is a bijection of 64 bit words, so the $S_i$ are distinct: strictly this is sampling without replacement from $2^{64}$ seeds, whose finite population correction $1 - N/2^{64} \approx 1 - 10^{-14}$ is negligible. What cannot be proven is that a fixed pseudo-random sequence is "random enough" for this integrand; that is the standard Monte Carlo assumption. Its testable consequence (folds of the seed sequence agree within their standard errors) is checked by the 8 fold chi-square test in `certify.fold_check`.

**A2 [A] (angle offset).** The per seed offset $U_i = \mathrm{splitmix64}(S_i \oplus c)/2^{64}$ behaves as uniform and independent of the map $\beta_{S_i}$ and spawn $p(S_i)$.

Under A1 and A2, the per seed pairs $(X_i, E_i)$ are iid with the law of $(X, E)$ in section 1.3, and they are bounded: $0 \le X_i \le J(R - R_0)$, $0 \le E_i \le J$. Write $\mu = \mathbb E[E_i] > 0$ (A3).

The estimator is $\hat M_N = \sum_{i \le N} X_i / \sum_{i \le N} E_i$ (undefined if no events).

### 3.2 Consistency

**Theorem 6 [P | A1, A2, A3] (strong consistency).** $\hat M_N \to M$ almost surely. The same estimator applied to stride $k$ data converges almost surely to $M_k$.

*Proof.* Bounded iid variables have finite means; by the strong law $\bar X_N \to \mathbb E X$ and $\bar E_N \to \mu > 0$ a.s., so $\sum E_i > 0$ eventually and $\hat M_N = \bar X_N/\bar E_N \to M$ (continuous mapping). The stride $k$ data are a different bounded iid sequence with means $(A_k J, B_k J)$. $\square$

**Corollary [P] (sparse alone is inconsistent for the exact model).** $\hat M^k_N - M \to M_k - M$ a.s. The error converges to a constant that depends on $k$ and the map, not on $N$. More seeds cannot remove it; only $k \to 1$ or the two phase correction (Theorem 10) can. **So the "+43%" is not seed noise: it is an estimate of the fixed number $M_4/M_1 - 1$.** Its estimator $\hat M^4_N / \hat M^1_N$ is consistent for that number by Theorem 6 and continuous mapping, and its paired confidence interval (both levels on the same seeds) is valid by Theorem 8 applied to the pair. The pilot's ratio interval was printed by `exact_analyze.py` but not saved; the production run will report it.

### 3.3 Finite sample bias

$\hat M_N$ is a ratio of means, so it is **not** unbiased, and strictly its expectation does not exist because $\sum E_i = 0$ has positive probability. The right statement:

**Theorem 7 [P | A1, A2, A3].** Let $G_N = \{\bar E_N \ge \mu/2\}$ and $Z_i = X_i - M E_i$. Then $P(G_N^c) \le \exp(-N\mu^2/(2J^2))$ and

$$ \mathbb E\big[(\hat M_N - M)\mathbf 1_{G_N}\big] = \frac{M\operatorname{Var}(E_1) - \operatorname{Cov}(X_1, E_1)}{N\mu^2} + O(N^{-3/2}). $$

*Proof.* Hoeffding on $E_i \in [0, J]$ gives the tail. $\hat M_N - M = \bar Z/\bar E$ and the exact identity $\frac1{\bar E} = \frac1\mu - \frac{\bar E - \mu}{\mu^2} + \frac{(\bar E - \mu)^2}{\mu^2 \bar E}$ give three terms. The first has mean $-\mathbb E[\bar Z \mathbf 1_{G_N^c}]/\mu$, of size $\le \|Z\|_\infty P(G_N^c)/\mu$ (exponentially small). The second has mean $-\operatorname{Cov}(\bar Z, \bar E)/\mu^2 = -\operatorname{Cov}(Z_1, E_1)/(N\mu^2) = (M\operatorname{Var}E_1 - \operatorname{Cov}(X_1,E_1))/(N\mu^2)$, up to the same exponentially small correction. On $G_N$ the third is at most $2|\bar Z|(\bar E - \mu)^2/\mu^3$, whose mean is $\le 2 (\mathbb E\bar Z^2)^{1/2} (\mathbb E(\bar E - \mu)^4)^{1/2}/\mu^3 = O(N^{-1/2})\,O(N^{-1})$ by Cauchy-Schwarz and the fourth central moment of a mean of bounded iid variables. $\square$

Size: the relative bias is of the order of $1/(\text{number of events})$. For the pilot (300 to 700 events for the rare biomes) that is about 0.3%, far below its 8% standard error; for the production runs it is below 0.05%. Test: `test_finite_sample_bias_matches_leading_term` (predicted 197, observed $194 \pm 10$ blocks on a synthetic world with known $M$).

### 3.4 Asymptotic normality and the confidence interval

**Theorem 8 [P | A1, A2, A3] (CLT and interval validity).**

$$ \sqrt N(\hat M_N - M) \Rightarrow \mathcal N(0, \sigma^2), \qquad \sigma^2 = \frac{\operatorname{Var}(X_1 - M E_1)}{\mu^2}, $$

and with $\hat\sigma^2 = \frac{N^2}{N-1}\,\sum_i (X_i - \hat M_N E_i)^2 \big/ \big(\sum_i E_i\big)^2$, the interval $\hat M_N \pm z_{1-\alpha/2}\hat\sigma/\sqrt N$ has coverage $\to 1 - \alpha$.

*Proof.* Bivariate CLT for the bounded iid pairs $(X_i, E_i)$, then the delta method for $g(a, b) = a/b$ at $(\mathbb E X, \mu)$, whose gradient $(1/\mu, -M/\mu)$ gives $\sigma^2$. $\hat\sigma^2 \to \sigma^2$ a.s. by the strong law and continuous mapping; Slutsky gives coverage. Correlation between the $J$ rays of a seed is included because the unit is the seed. $\square$

What is *not* proven: a rate for the coverage error with explicit constants. For smooth functions of means the two sided coverage error is $O(1/N)$ (Edgeworth expansion), but the constant depends on unknown moments. The repo refuses to certify with fewer than 30 events and cross-checks the delta SE with a seed cluster bootstrap (`certify.boot_se`); test: `test_delta_ci_coverage` (coverage 0.93 to 0.97 at 800 seeds).

**Theorem 9 [P | A1, A2, A3] (a confidence interval valid for every $N$).** For fixed $m$, $Z_i(m) = X_i - m E_i$ are iid in an interval of length $b(m) = J(R - R_0 + m)$, and $\mathbb E Z_i(M) = 0$. Let $V_N(m)$ be their sample variance, $\ell = \ln(4/\alpha)$ and

$$ h(m) = \sqrt{2 V_N(m)\,\ell/N} + \frac{7\, b(m)\,\ell}{3(N-1)} - |\bar Z_N(m)|. $$

Then $C_N = \{m \ge 0 : h(m) \ge 0\}$ satisfies $P(M \in C_N) \ge 1 - \alpha$ for every $N \ge 2$.

*Proof.* The empirical Bernstein inequality (Maurer and Pontil 2009, Theorem 4) applied to $Z_i(M)$ and to $-Z_i(M)$, each at level $\alpha/2$, gives $P(h(M) < 0) \le \alpha$. $\square$

Computing it exactly: $\sqrt{V_N(m)}$ is a Euclidean norm of a vector affine in $m$, hence convex, and $|\bar Z_N(m)|$ is linear on each side of $\hat M_N$. So $h$ is convex on $[0, \hat M_N]$ and on $[\hat M_N, \infty)$, $h(\hat M_N) > 0$, and each side's accepted set is an interval whose end is found by bisection (if the asymptotic slope of $h$ is $\ge 0$ the set is unbounded above, which is the honest answer when there are too few events). `theory.eb_ratio_ci` implements this; test: `test_empirical_bernstein_ci_has_finite_sample_coverage` (coverage 100% at 60 seeds where the delta interval is at 95%, width about 1.7 times the delta interval at 40,000 seeds). It is not used by the pipeline yet; it is the interval to quote if a guarantee that does not rely on "N is large enough" is wanted.

### 3.5 The two phase estimator

**Theorem 10 [P | A1, A2, A3].** With $N$ seeds at stride $k$ and the first $n_c$ of them also exact,

$$ \hat M = \hat M_k(\text{all } N) + \big[\hat M_1(\text{first } n_c) - \hat M_k(\text{first } n_c)\big] \to M_k + (M - M_k) = M \text{ a.s. as } N, n_c \to \infty, $$

with asymptotic variance $\big(\operatorname{Var}(u) + 2\operatorname{Cov}(u, v)\big)/N + \operatorname{Var}(v)/n_c$, where $u$ is the stride $k$ influence function and $v = \mathrm{IF}_1 - \mathrm{IF}_k$ on the calibration seeds.

*Proof.* A prefix of an iid sequence is an iid sample whose index set does not depend on the values, so Theorem 6 applies to each of the three ratios. Linearising each ratio as in Theorem 8, $\hat M - M \approx \frac1N\sum_{i \le N} u_i + \frac1{n_c}\sum_{i \le n_c} v_i$; $\operatorname{Cov}\big(\frac1N\sum_{i\le N} u_i, \frac1{n_c}\sum_{i \le n_c} v_i\big) = \frac{n_c}{N n_c}\operatorname{Cov}(u,v) = \operatorname{Cov}(u,v)/N$, which enters twice. $\square$ (Implemented by `certify.build_terms_stride`, tested in `tests/test_certify.py`.)

### 3.6 Conditions under which the guarantees break

* **Optional stopping.** Theorems Theorem 8 and Theorem 9 assume $N$ fixed before looking at the result. Choosing $N$ from the production data until the interval looks good voids them. The plan (fix $N$ from a pilot on different seeds) respects this.
* **Rankings are many claims at once.** A 95% interval per biome does not make the ranking 95% correct. A rank swap between biomes $a$ and $b$ should be judged on $\hat M_a - \hat M_b$ with the delta method applied to the pair (the same seeds give both, so the covariance is estimated from the same seed clusters), and with a multiplicity correction if several swaps are claimed together.
* **Reusing seeds across estimates that are then treated as independent.** See section 4, item 1.

## 4. The code computes the model

**Claim.** For each biome and radius, the number the pipeline prints from seeds $s_0, \dots, s_0 + N - 1$ equals $\hat M_N$ of section 3, evaluated at seeds $S_i = \mathrm{splitmix64}(s_0 + i)$ and offsets $U_i$, up to a rounding error bounded in Proposition 12. Combined with Theorem 6 under A1 and A2, the printed number converges almost surely to $M$ (exact level) or $M_k$ (stride $k$), and the interval of Theorem Theorem 8 or Theorem 9 applies.

The argument is a step by step refinement: each row says which model object the code step computes and why.

| # | code | model object | argument | status |
|---|---|---|---|---|
| 1 | `worker`: `seed = splitmix64(seed0 + i)` | $S_i$ | bijection, so distinct within a run | [C], A1 for randomness |
| 2 | `u = splitmix64(seed ^ c) >> 11 / 2^53`, `ang = 2π(k+u)/rays` | $U_i$, $\theta_j$ | $2^{-53}$ grid on $[0,1)$; $J$ equally spaced rays | [C], A2 |
| 3 | `estimateSpawn` | $p(S)$ | definition of the model | [C] (gap vs the game: item 13) |
| 4 | `surface_only(qx, qz)` (hint free) | $\beta_S(q)$ | definition; same arithmetic in colsim and discexact; hint free, so the value depends only on the cell, not on the path | [C] |
| 5 | `x0 = 4qx - 0.5, x1 = x0 + 4` | $Q_q$ | identical to section 1.2 | [C] |
| 6 | `rho_to`, the `rho <= r` branch of `cell_D` | visible case of $D(Q_q, r)$ | distance to an axis aligned box | [C], `test_discexact` rho rule tests |
| 7 | `line_interval` | $\{s : \operatorname{dist}(p + su, Q_q) \le r\}$ | $Q \oplus B_r$ is the union of two rectangles and four corner discs; the set is an interval because $s \mapsto \operatorname{dist}(p+su, Q)$ is convex; the union of the pieces' intervals is that interval, so its minimum is the entry time | [P] + brute force comparison in `test_discexact.py` and `test_python_cell_D_matches_bruteforce` |
| 8 | `s = max(lo, 0)`, `hi < 0` means never | $s^*$ | in the non visible branch $\operatorname{dist}(p, Q) > r$, so $lo > 0$ whenever $hi \ge 0$; `max` is only a guard | [P] |
| 9 | `scan_ray` enumerates cells | all $q$ with $D(Q_q, r) \le R$ | such a cell has a point within $r$ of the segment $\{p + su : 0 \le s \le R\}$. The code takes every cell column meeting the segment's bounding box widened by $m = r_{\max} + 6$, and in each column the band of half width $m/\lvert u_x\rvert$ around the line, which contains every point within distance $m$ of the line; the extra 6 blocks absorb the half block cell offset in `floor(z/4)` | [P] + completeness test against a box scan in `test_discexact.py` |
| 10 | `emit_min`: `qx % k == 0 && qz % k == 0`, running min | $D(S_k(b), r)$ and, for $k=1$, $D(P_b, r)$ | Lemma 3(c); levels are nested (Theorem 1) | [C], per ray monotonicity test |
| 11 | `D <= cap ? D : -1`, cap $=$ `rmax` | censoring at $R$ | $x$ and $e$ depend on $d$ only through $\min(d, R)$ and $\mathbf 1\{d \le R\}$, so replacing every $d > R$ by $\infty$ changes nothing. **Precondition: `--rmax` equals the $R$ used in the analysis (both 20000 by default).** | [P] |
| 12 | `di = floor(D + 0.5)` | $\tilde D$, $\lvert\tilde D - D\rvert \le \tfrac12$ | Proposition 12 | [P], `test_rounding_changes_M_by_at_most_the_bound` |
| 13 | `certify.stats` | $(X_i, E_i)$ | `E = (D>=R0)&(D<=R)`, `X = where(D>=R0, min(D,R)-R0, 0)`, summed over the rays of a seed: identical to section 1.3 | [C], `test_certify.py` |
| 14 | `certify.combo` | $\hat M_N$ and $\hat\sigma/\sqrt N$ | `z_i = (X_i - m E_i)/ΣE`, variance `Σ z_i² · N/(N-1)`: exactly Theorem 8's $\hat\sigma^2/N$ | [C], `test_delta_ci_coverage` |
| 15 | `certify.build_terms_stride` | Theorem 10 | checks that the calibration rows are the first $n_c$ main seeds | [C], `test_certify.py` |
| 16 | `load_nested`, `exact_analyze.py` | seed index | rows are placed into a (seed, ray) matrix by assignment, so a seed that appears in two overlapping chunks is counted once, not twice | [C] |

**Proposition 12 [P] (integer rounding).** Let $\tilde D = \lfloor D + \tfrac12 \rfloor$ and $\tilde M$ the window functional of $\tilde D$ (for the true law or for the empirical law of any sample). Then

$$ |\tilde M - M| \le \frac{a + M\,\varepsilon}{\tilde B}, \qquad a = \tfrac12 P(D \ge R_0 - \tfrac12), \quad \varepsilon = P\big(|D - R_0| \le \tfrac12 \text{ or } |D - R| \le \tfrac12\big). $$

*Proof.* $x$ is 1-Lipschitz and constant outside $[R_0, R]$, so $|x(\tilde D) - x(D)| \le \frac12\mathbf 1\{D \ge R_0 - \frac12\}$; $e$ can only flip within half a block of $R_0$ or $R$; insert into Theorem 2(b). $\square$ Under H, with $q = e^{-L/M}$, the relative error is about $\big(\frac{1}{2(1-q)} + \frac{1+q}{1-q}\big)/M \approx \max(1.5/M,\ 2.5/L)$: below $2 \times 10^{-4}$ whenever $M \ge 10^4$, which covers every rare biome reported (common biomes with $M \approx 10^3$ get about $10^{-3}$). Floating point in the geometry (doubles, coordinates below $3 \times 10^4$) perturbs $D$ by about $10^{-11}$ blocks and is covered by the same bound.

### 4.1 Gaps: where the code and the model differ, or the model and the game differ

1. **Seed reuse (code vs independence).** The exact pilot used seeds $7\times10^9, \dots, 7\times10^9 + 599$, which are also the first 600 seeds of the certified centerline run (`cert_pipeline.PROD_SEED0`). Inside either estimator this is harmless. It matters only if the two are compared as if independent (their errors are positively correlated). The production exact run should use fresh seeds (HANDOFF suggests $9\times10^9$), or the comparison should be paired on purpose.
2. **The certified centerline numbers estimate the step 1 walk, not the exact centerline.** `colsim` looks at the block containing $p + su$ only at integer $s$.

   **Proposition 11 [P].** Let $D^{\rm step1}$ be that first hit. Then $D_{b,0} \le D^{\rm step1}_b$, and $D^{\rm step1}_b < D_{b,0} + 1$ whenever the ray's first run inside $P_b$ is at least one block long.

   *Proof.* $\lfloor x + \frac12 \rfloor$ is the block containing $x$, so a hit at integer $s$ means $p + su \in P_b$, hence $D_{b,0} \le s$. A run of length $\ge 1$ starting at $D_{b,0}$ contains an integer. $\square$ Test: `test_step1_walk_is_within_one_block_when_chords_are_long`.

   So the step 1 walk is itself a sparse sample (in $s$ instead of in cells), and Theorems 1, 2 and Theorem 6 apply to it unchanged: $\hat M^{\rm step1}_N \to M^{\rm step1}$, which is $\ge M_0$ under H. The difference comes only from crossings shorter than one block (corner clips). For an isolated 4x4 cell, 12% of isotropic line crossings are shorter than one block and 6.0% would be missed (integer positions at a uniformly random phase); for multi-cell patches only the patch corners contribute, so the effect is smaller, but it is not zero. **[E]** Pilot exact $r=0$ pale garden $107{,}479$ ($\pm \approx 8\%$) versus certified step 1 $113{,}877$ ($\pm 1.9\%$): no significant difference at pilot precision. Because the seeds overlap (gap 1), a paired comparison on those 600 seeds is available and is the right way to measure $M^{\rm step1}/M_0$.
3. **Truncation at $R$.** Everything proven is about $M$ on $[R_0, R]$. Reading $M$ as a mean walk beyond $R$ needs H (section 1.4). Checked on the window by `bin_hazards`; beyond $R$ only for 12 biomes up to 100k on the centerline (`flat.py`).
4. **Stride.** Fully covered by Theorems 1 to 3, Theorem 6 and Theorem 10: a known, signed (up to Theorem 2(c)), $N$ independent bias, removable by the two phase estimator.
5. **Discretisation of the map.** None relative to the block model (Lemma 3(c)). The path is continuous in the exact program; no step size enters.
6. **Model vs game (outside this document's proofs).** Spawn is `estimateSpawn`, not the game's spawn search; the surface biome is the depth 0 layer of the climate sample, not the biome at the actual terrain height; distance is horizontal only; no line of sight. These define the model. Whether they match what a player sees is a modelling question that no amount of mathematics about the code can settle.

## 5. Summary

| statement | status |
|---|---|
| Cell model equals block model | [P] Lemma 3(c) |
| Sparse first hit is never earlier: $D \le D^k$ per ray | [P] Theorem 1 |
| Sparse bias $M_k - M$ is $\ge 0$ | **not true in general** [P] Theorem 2(d); true under H or hazard ordering [P \| H] |
| Negative sparse bias is at most $M\,p_{\rm in}/B_k$ | [P] Theorem 2(c) |
| Sparse bias at most $2\Delta/(w + 2r - 2\Delta)$ relative, decaying as $O(1/r)$ | [P \| F, H, Steiner] Corollary 5 |
| Pale garden sparse bias +43% / +9% / +7.8% at $r = 0 / 64 / 128$ | [E] 600 seeds; a consistent estimate of a fixed number, not noise |
| Exact estimator converges a.s. to $M$; sparse converges to $M_k \neq M$ | [P \| A1, A2, A3] Theorem 6 |
| Exact estimator bias is $O(1/N)$ with explicit leading term | [P \| A1, A2, A3] Theorem 7 |
| Delta interval has asymptotic coverage $1-\alpha$ | [P \| A1, A2, A3] Theorem 8 |
| Empirical Bernstein interval has coverage $\ge 1-\alpha$ for every $N$ | [P \| A1, A2, A3] Theorem 9 |
| Two phase estimator is consistent for the exact $M$ | [P \| A1, A2, A3] Theorem 10 |
| discexact computes $D(P_b, r)$ and $D(S_k(b), r)$ exactly up to rounding $\le \frac12$ block | [P] + [C] section 4 |
| Rounding moves $M$ by less than $2\times10^{-4}$ relative | [P] Proposition 12 |
| Certified centerline targets the step 1 walk, $\ge$ exact centerline under H | [P] Proposition 11 |
| Seeds behave as iid uniform | [A] A1, tested by fold chi-square |
| $M$ is a mean walk beyond 20,000 blocks | [A] H |
| The model matches the game | [A] section 4.1 item 6 |
| `certrun.py` intervals all hold at once with prob $\ge 1-\alpha$, at any stopping time | [P \| A1, A2] Theorems 16, 17 |
| `certrun.py` computes those intervals from exactly the planned seeds and the exact model | [P] + [C] section 6.3, re-checked by `verify` |

## 6. The certified sampler (`certrun.py`)

*Section 7 replaces the interval (6.1) and the planning (6.2) below with a cheaper scheme that keeps the guarantee; the integrity checks of 6.3 and the `verify` re-derivation are unchanged.*

The sampler is built so that every hypothesis of a theorem is enforced by code, not by discipline. It removes the three weaknesses found above: no sparse level is used (only level 1 rows, every cell), the centerline is the exact $r = 0$ model of `discexact` (not the step 1 walk of Proposition 11), and the intervals are valid for the planned $N$, not only as $N \to \infty$.

### 6.1 What is certified

Fix a list of biomes $\mathcal B_0$ (all 94 in `out/names.csv`) and radii $\mathcal R_0$ (default $0, 64, 128$). The $K = |\mathcal B_0|\,|\mathcal R_0|$ quantities are the exact window functionals $M_{b,r}$ of section 1.3. For each, the report gives $C_{b,r}$, the empirical Bernstein set of Theorem 9 at level $\alpha/K$, computed from the production seeds.

**Theorem 13 [P | A1, A2] (simultaneous coverage for the planned N).** Let the pilot use seed indices $I_p$ and production use $I = \{s_0, \dots, s_0 + N - 1\}$ with $I \cap I_p = \emptyset$, and let $N$ be any function of the pilot data. Then

$$ P\big(M_{b,r} \in C_{b,r} \text{ for all } (b, r) \in \mathcal B_0 \times \mathcal R_0\big) \ge 1 - \alpha. $$

*Proof.* Under A1 the seeds with indices in $I_p$ and in $I$ are independent, so conditionally on the pilot data $N$ is a constant and the production pairs $(X_i, E_i)_{i \in I}$ are still iid with the unconditional law. Theorem 9 at level $\alpha/K$ applies to each $(b, r)$ conditionally on the pilot; the union bound over the $K$ failure events gives $\ge 1 - \alpha$ conditionally, hence unconditionally. If $\mathbb E[E] = 0$ for some $(b, r)$ the data have no events, the set is $[0, \infty)$ and the claim is vacuous rather than false (convention $M = \infty$). $\square$

A3 is not needed: a biome with too few events gets an unbounded interval, which is correct, not an error.

**Corollary 14 [P | A1, A2] (certified ranking).** On the event of Theorem 13, $\inf C_{a,r} > \sup C_{b,r}$ implies $M_{a,r} > M_{b,r}$. So all orders listed in `certified_order` hold simultaneously with probability $\ge 1 - \alpha$, with no further multiplicity correction (they are consequences of the one event).

What Theorem 13 does not need: H, the Steiner model, F, or "N large". What it still needs: A1 and A2 (section 3.1), and the definition of the model (section 4.1 item 6). Under H, each certified $M$ is also a certified mean extra walk; without H it is a certified inverse hazard on the window.

### 6.2 Planning (affects only the width, never the coverage)

From a pilot, the half width of $C$ at $N$ seeds is predicted by solving $|\bar Z_N(m)| = \text{bound}(m)$ near $\hat M$:

$$ \frac{\text{half width}}{\hat M} \approx \frac{\sqrt{2 V \ell / N} + 7 J (R - R_0 + \hat M)\,\ell / (3(N-1))}{\bar E\,\hat M}, \qquad \ell = \ln(4K/\alpha), $$

with $V$, $\bar E$, $\hat M$ from the pilot. `required_N` takes the smallest $N$ meeting the target for every target biome and radius, times 1.10. Because $N$ depends only on pilot seeds, Theorem 13 holds whatever the pilot says; a noisy pilot can only make the final interval wider or narrower than planned.

**[E] The committed plan** (`out/certrun/plan.json`): pilot on seed indices $8\times10^9, \dots, 8\times10^9 + 199$; target $\pm 5\%$ for the six rare biomes at every radius, $K = 282$, $\alpha = 0.05$ (so $\alpha/K = 1.8\times10^{-4}$ each). Required $N$ ranges from 8,817 (stony peaks, $r = 128$) to 30,028 (mushroom fields, $r = 0$); the plan fixes $N = 30{,}028$ seeds $\times$ 4 rays on indices from $9\times10^9$. At 1.15 s CPU per ray (all three radii together) that is about 38 CPU hours: about 2.4 hours on 16 threads. The finite $N$ guarantee costs about $1.7\times$ the width of the asymptotic interval per quantity and a further factor $\sqrt{\ln(4K/\alpha)/\ln(4/\alpha)} \approx 1.5$ for simultaneity over 282 quantities, hence the larger $N$ than the earlier $\pm 2\%$ single-biome asymptotic plan.

### 6.3 The code computes Theorem 13's sets

| step | code | why it is the model |
|---|---|---|
| seeds | `seed_of` (Python splitmix64), `check_integrity` | the report recomputes every planned seed and refuses unless the data contain exactly those seeds: so the data are $S_{s_0}, \dots, S_{s_0 + N - 1}$ with the planned $N$, no duplicates, no extra or missing seeds, no optional stopping. The end to end test confirms Python and C produce the same seeds |
| fresh seeds | `check_fresh`, `ledger.json`, `HISTORICAL` | planning refuses any production or pilot range overlapping an earlier one (both historical runs are listed), which is the hypothesis $I \cap I_p = \emptyset$ |
| plan fixed | `plan_hash` | `run` and `report` refuse a `plan.json` edited after planning; `plan` refuses to overwrite an existing plan |
| complete files | spawn row check | the spawn cell is always visible ($\rho = 0 \le r$), so every (seed, ray, radius) has a row with $D = 0$; a missing one proves a truncated or foreign file |
| exact model | `load_csv` keeps `level == 1` | every cell; $r = 0$ is the exact centerline (Lemma 3, section 4 rows 5 to 11) |
| censoring | `report` requires `rmax == R` | section 4 row 11 |
| $(X_i, E_i)$ | `per_seed_EX` | rows are found rays; a missing ray is $D = \infty$, contributing $x = R - R_0$, $e = 0$. Equal to `certify.stats` on the dense matrix (`test_per_seed_EX_matches_dense_stats`) |
| $C_{b,r}$ | `interval` = `theory.eb_ratio_ci` at `alpha / K` | Theorem 9, exact bisection (section 3.4) |
| ranking | `certified_order` | Corollary 14 (`test_ordering_needs_disjoint_intervals`) |

**Independent re-derivation on production rays (`certrun.py verify`).** For random production (seed, ray) pairs it reruns `discexact --debug`, which prints every enumerated cell with its biome and $D$ per radius, and then, in Python code that shares nothing with `discexact.c`:

1. recomputes $D(Q_q, r)$ for every printed cell with `theory.cell_D` (tested against brute force minimisation);
2. builds its own superset of the cells within $r_{\max}$ of the segment and checks that every one with finite $D$ was enumerated by C. The superset is complete because a point $y$ within $r$ of the segment has a nearest segment point $L(s)$ with $|y_x - L(s)_x| \le r$ and $|y_z - L(s)_z| \le r$, so $s$ lies in the parameter range where the line is within $r$ of the cell's column, and $y_z$ lies within $r$ of the line's $z$ values on that range (plus one cell of margin on each side);
3. takes the per biome minimum, rounds it, and checks it equals the production row.

**[E] On the pilot:** 4 rays, 1,311,096 cells, largest $|D_{\rm C} - D_{\rm Python}| = 5\times10^{-7}$ (the C debug output prints 6 decimals), 0 missing cells, 0 row mismatches. Running `verify` on a few production rays after the run turns the code to model argument of section 4 into a check on the very data being certified.


## 7. Making it cheaper without losing the guarantee

### 7.1 Where the time goes (profiled)

| measurement | value |
|---|---|
| share of run time in the biome lookup (`surface_only`) | 98% (same run with the lookup replaced by a constant: 0.38 s instead of 18 s) |
| time per lookup | 3.26 µs (one 2.1 GHz Xeon core) |
| cells looked up per ray, $R = 20000$ | 5,573 for radii $\{0\}$; 165,910 for $\{0, 64\}$; 326,829 for $\{0, 64, 128\}$ |
| fitted cells per ray | $5573 + 2510\, r_{\max}$ (all smaller radii come free with the largest) |
| per seed overhead (generator setup, `estimateSpawn`) | 3.7 ms |
| `-O3 -march=native -ffp-contract=off`, LTO | 5 to 9% faster, output bit-identical on this machine (not adopted, see 7.5) |

So the cost of one ray is $c(r_{\max}) = 3.26\,\mu s \times (5573 + 2510\, r_{\max})$: **0.018 s at $r_{\max} = 0$, 0.54 s at 64, 1.07 s at 128.** The centerline is 60 times cheaper than the 128 capsule, and the old plan paid the 128 price for every seed because one seed count served all radii.

**Rays per seed do not matter [P + E].** With $J$ rays per seed, cost is $N J c$ and $\operatorname{Var}\hat M \approx \sigma^2_{\rm ray}\,\mathrm{deff}/(N J)$ with design effect $\mathrm{deff} = 1 + (J - 1)\bar\rho$. Cost times variance is $c\,\sigma^2_{\rm ray}\,\mathrm{deff}$ plus the per seed overhead ($3.7$ ms against $J \times 1$ s, negligible), so $J$ matters only through $\bar\rho$. In the pilot the 18 target quantities have $\mathrm{deff}$ between 0.81 and 1.23 (noise at 200 seeds) and ray correlations between $-0.10$ and $+0.11$. $J = 4$ is kept.

### 7.2 A tighter interval that is valid at every N: betting confidence sequences

For one quantity, with seeds in index order $t = 1, 2, \dots$, an indicator $\iota_t \in \{0, 1\}$ (the seed is in this quantity's stream) and bets $\lambda^\pm_t \in [0, \tfrac12]$, define for $m > 0$

$$ K^+_t(m) = \prod_{s \le t} \Big(1 + \iota_s \lambda^+_s \frac{X_s - m E_s}{J m}\Big), \qquad K^-_t(m) = \prod_{s \le t} \Big(1 - \iota_s \lambda^-_s \frac{X_s - m E_s}{J (R - R_0)}\Big), $$

and $C_t = \{ m > 0 : K^+_t(m) < 2/\alpha_q \text{ and } K^-_t(m) < 2/\alpha_q \}$.

**Theorem 16 [P | A1, A2] (anytime valid confidence sequence).** Let $\mathcal F_t$ be everything computed from seeds $1, \dots, t$ (all biomes, all radii). If $\iota_t$, $\lambda^+_t$, $\lambda^-_t$ are $\mathcal F_{t-1}$ measurable and do not depend on the argument $m$, then $P(\exists t : M \notin C_t) \le \alpha_q$. Moreover each $C_t$ is an interval $(\ell_t, u_t)$, found exactly by bisection.

*Proof.* Factors are $\ge \tfrac12$: $(X - mE)/(Jm) \ge -E/J \ge -1$ and $(X - mE)/(J(R - R_0)) \le X/(J(R-R_0)) \le 1$. At $m = M$, seed $t$ is independent of $\mathcal F_{t-1}$ (A1) and $\mathbb E[X_t - M E_t] = 0$, so $\mathbb E[\text{factor}_t \mid \mathcal F_{t-1}] = 1$: $K^\pm_t(M)$ are nonnegative martingales with $K_0 = 1$. Ville's inequality gives $P(\sup_t K^\pm_t(M) \ge 2/\alpha_q) \le \alpha_q/2$ for each sign; add the two. Monotonicity: every factor of $K^+$ is positive and nonincreasing in $m$ ($X_s \ge 0$), every factor of $K^-$ positive and nondecreasing, so $\{K^+ < c\}$ is an up-set, $\{K^- < c\}$ a down-set, and their intersection an interval. $\square$

Because the statement is uniform in $t$, it holds at any stopping time: **stopping as soon as the interval is narrow enough is allowed**, with no correction. The bets used (`theory.BettingCS`) are $\lambda_t = \min\big(\tfrac12, \sqrt{2\ln(2/\alpha_q)/(n^* \hat v_{t-1})}\big)$, where $\hat v_{t-1}$ is the variance of the normalised increment over seeds before $t$ (at the plug-in $\hat M_{t-1}$, shrunk toward a pilot value), and $n^*$ is the planned horizon. Any other predictable choice would also be valid; this one only makes the interval narrow near $n^*$. Tests: `test_cs_covers_at_every_time_at_once`, `test_wealth_is_monotone_so_the_set_is_an_interval`, `test_bets_are_predictable`, `test_excluded_seeds_do_not_bet`.

**[E] Width.** On worlds resampled from the pilot at 20,000 seeds and $\alpha_q = 0.05/282$: mushroom fields $r=0$ half width 4.6% (empirical Bernstein: 6.0%), pale garden $r=64$ 3.3% (4.1%), mushroom fields $r=128$ 3.4% (4.3%). About 22% narrower, so about 40% fewer seeds for the same width. The asymptotic Bonferroni CLT interval (not valid at finite $N$) is a further 13% narrower: that is the price of the finite $N$ guarantee.

**Theorem 17 [P | A1, A2] (the certificate).** Give each of the $K$ quantities its own level $\alpha_q$ with $\sum_q \alpha_q \le \alpha$, its own stream indicator and bets as in Theorem 16, and let the run stop at any stopping time of $(\mathcal F_t)$. Then with probability $\ge 1 - \alpha$, every $M_q$ is in its final interval, simultaneously.

*Proof.* Every $K^\pm_{q}$ is a martingale for the same joint filtration $\mathcal F_t$, because the streams' indicators and bets are $\mathcal F_{t-1}$ measurable even when they depend on other quantities' data. Union bound over the $K$ events of Theorem 16. The final intervals are $C_{q, \tau}$ at the stopping time $\tau$, covered by "for all $t$". $\square$ Test: `test_simultaneous_coverage_with_unequal_alpha`. Corollary 14 (certified orders) carries over unchanged.

Three free choices follow, none of which can affect validity: the split $\alpha_q$, the stream indicators (which radii each seed computes), and when to stop.

### 7.3 Choosing the free parameters to minimise cost

* **Nested streams.** A seed computed at $r_{\max}$ gives every smaller radius for free. Seed $t$ computes radii $\{ r \le \max \mathcal A_t \}$, where $\mathcal A_t$ is the set of radii still *active* (some target at that radius is wider than the target, and the radius is below its cap $n^{\max}_r$), decided from earlier chunks only (`next_radii`). So $\iota_t$ is predictable.
* **Alpha split.** The 264 non-target quantities share $\alpha_{\rm rest} = 0.005$; they still get valid simultaneous intervals, just wider. The 18 targets share $0.045$. With the planning model $N_q(\alpha_q) = A_q \ln(2/\alpha_q)$, $A_q = 2\kappa_q^2 V_q / (\text{target}\,\bar E_q m_q)^2$ ($V_q$, $\bar E_q$, $m_q$ from the pilot, $\kappa_q$ the measured ratio of the betting width to its leading term), `optimise` minimises
$$ J \sum_{r} c(r)\,(N_r - N_{r^+}) \quad\text{subject to}\quad \sum_q 2 e^{-N_{r(q)}/A_q} \le 0.045,\ N_0 \ge N_{64} \ge N_{128}, $$
($r^+$ the next larger radius) over a grid. This is the Lagrangian trade: more $\alpha$ goes to quantities that are expensive to tighten (rare biomes at the large, costly radii), less to cheap ones.
* **Stopping.** The run stops each radius as soon as all its targets are met (or at $n^{\max}_r = 2 n^*_r$). With a confidence sequence the plan needs no safety margin: if the pilot was optimistic the run continues, if pessimistic it stops early.

**[E] The committed plan** (`out/certrun/plan.json`, same pilot seeds $8\times10^9 + [0, 200)$, production from $9\times10^9$): $n^*_{128} = 5{,}530$, $n^*_{64} = 6{,}427$, $n^*_0 = 12{,}635$ seeds, **expected 7.2 CPU hours instead of 38** (about 27 minutes on 16 threads), cap 14.4 CPU hours. The $\alpha_q$ of the targets range from $4.5\times10^{-6}$ (stony peaks, $r = 0$: easy, so it gets little) to $1.5\times10^{-2}$ (mushroom fields, $r = 64$).

### 7.4 What the reduction is made of (approximate)

| change | effect on cost | guarantee |
|---|---|---|
| betting confidence sequence instead of empirical Bernstein | about 0.6x seeds | Theorem 16 |
| $\alpha$ split toward the 18 targets, optimised | about 0.75x seeds | Theorem 17 (any split with $\sum \alpha_q \le \alpha$) |
| separate seed counts per radius (centerline is 60x cheaper) | most $r = 0$ seeds at 1/60 of the cost | Theorem 17 (predictable stream indicators) |
| stop when met, no 1.10 margin | about 0.9x, adapts to the truth | Theorem 16 (anytime) |
| rays per seed | none | any $J$ |

### 7.5 Considered and not adopted

* **Skipping lookups with partial climate.** Biome assignment is a nearest-point search over climate boxes in 6 dimensions, so knowing one parameter (say continentalness) does not exclude a biome without a bound on the others. A correct pruning rule needs its own proof; not done.
* **Sparse sampling plus a calibration subset (Theorem 10).** Sparse levels only save time if unsampled cells are not looked up, and a finite $N$ version needs a confidence sequence for a difference of ratios. Possible, not done; the $r = 0$ calibration term was large in the pilot.
* **A larger window $R$.** More events per unit cost, but it changes the estimand unless H holds.
* **`-march=native` / LTO.** 5 to 9%; identical output here, but bit-identity across other CPUs would need its own argument (no `-ffast-math`, no FMA contraction, same libm). Not worth the risk for the gain.

**How far from optimal?** For a fixed cost per seed, no interval valid at every $N$ can beat the large deviation rate: the leading term $\sqrt{2 \ln(2/\alpha_q) V / N}$ is the Chernoff rate for a Gaussian-like mean. The betting sequence attains it up to $\kappa \approx 1.1$ to $1.3$. The remaining gap to the asymptotic CLT interval (about 1.3x in seeds) is the price of a guarantee that does not assume $N$ is large. This optimality statement is heuristic, not a theorem proved here. The real remaining lever is the cost per lookup (7.5, first item).


## 8. The walk from spawn, $\mathbb E[D]$, with no window (`certwalk.py`)

This replaces $M$ as the headline. Nothing before any distance is thrown away: every metre from spawn counts.

### 8.1 Estimand

For biome $b$, radius $r$, and start $p(S)$ (spawn), $D = D(P_b, r)$ from section 1.2 with $\inf\emptyset = \infty$. The estimand is $\mathbb E[D] \in [0, \infty]$.

**Theorem 18 [P] (exact split at any cap).** For every $C > 0$,
$$ \mathbb E[D] = A_C + S_C\, T_C,\qquad A_C = \mathbb E[\min(D, C)],\quad S_C = P(D > C),\quad T_C = \mathbb E[D - C \mid D > C] $$
(with $S_C T_C = 0$ if $S_C = 0$). Hence $\mathbb E[D] \ge A_C$, with no assumption at all.

*Proof.* $D = \min(D, C) + (D - C)\mathbf 1\{D > C\}$ pointwise, both terms $\ge 0$; take expectations (linearity holds in $[0, \infty]$ for non negative variables) and write $\mathbb E[(D - C)\mathbf 1\{D > C\}] = S_C T_C$. $\square$

So the cap changes nothing about the estimand. It only decides how much of $\mathbb E[D]$ is certified directly ($A_C$) and how much needs the tail ($S_C T_C$).

**Assumption $H_C$ [A] (constant hazard from $C/2$ on).** $P(D > t \mid D > C/2) = e^{-\lambda (t - C/2)}$ for $t \ge C/2$, some $\lambda > 0$.

**Proposition 19 [P | $H_C$].** Under $H_C$, $T_C = 1/\lambda$, and $1/\lambda$ equals the window ratio $M$ of section 1.3 computed on $[R_0, R] = [C/2, C]$.

*Proof.* Memorylessness of the exponential: given $D > C \ge C/2$, $D - C$ is exponential with rate $\lambda$, mean $1/\lambda$. The window ratio is $1/\lambda$ by the bullet after Lemma 1 with $R_0 = C/2$, $R = C$. $\square$

Without $H_C$ the error is confined to the tail term: $\mathbb E[D] - (A_C + S_C M_{[C/2, C]}) = S_C\,(T_C - M_{[C/2, C]})$. The plan picks $C$ so that the pilot tail share $S_C T_C / \mathbb E[D]$ is below 5% (for an exponential law $S_C T_C/\mathbb E[D] = e^{-C/\mathbb E[D]}$, so $C = \mathbb E[D] \ln 20 \approx 3\,\mathbb E[D]$). $H_C$ is checked by the 4 bin hazard table on $[C/2, C]$ in the report.

### 8.2 Three confidence sequences per arm

Per seed $i$ (rays $j = 1..J$): $W_i = \sum_j \min(D_{ij}, C) \in [0, JC]$, $K_i = \#\{j : D_{ij} > C\} \in [0, J]$, and $(E_i, X_i)$ the window pair of section 1.3 on $[C/2, C]$.

**Corollary [P | A1, A2] (means are a special case of Theorem 16).** Theorem 16 only uses that $0 \le X_i \le J(R - R_0)$, $0 \le E_i \le J$ and $\mathbb E[X_i - M E_i] = 0$. With $E_i \equiv J$, $R_0 = 0$ and $R = C$ (resp. $R = 1$), $X_i = W_i$ (resp. $K_i$) satisfies these with $M = A_C$ (resp. $S_C$). So the same betting construction gives anytime valid confidence sequences for $A_C$ and $S_C$; with $(E_i, X_i)$ on $[C/2, C]$ it gives one for $M_{[C/2,C]}$.

*Proof.* Substitute: $W_i - mJ \ge -mJ$ keeps $K^+$ factors $\ge 1 - \lambda^+ \ge \frac12$, and $W_i - mJ \le JC$ keeps $K^-$ factors $\ge \frac12$. The martingale argument of Theorem 16 is unchanged. $\square$

### 8.3 The spawn bias

Same seeds and the same angles, second arm: start $p_u(S)$ uniform on the cells of $[-L, L]^2$, drawn from its own splitmix stream of the seed (independent of the angle stream). $D_u$ is $D$ from $p_u$. The **spawn bias** is $\Delta = \mathbb E[D] - \mathbb E[D_u]$. Because the seeds are shared, the capped part is a paired mean: $V_i = W_i - W_{u,i} + JC \in [0, 2JC]$, $\mathbb E[V_i]/J = A_C - A_{u,C} + C$. The Corollary with $R = 2C$ gives a confidence sequence for $\Delta_C = A_C - A_{u,C}$, the spawn bias of the capped walk, with no tail assumption. Pairing removes the map to map variance shared by the two arms.

### 8.4 The certificate

**Theorem 20 [P | A1, A2] (simultaneous, any stopping time).** For each (biome, radius) run seven confidence sequences: $A, S, M_{[C/2,C]}$ for each arm and $\Delta_C$, each at its own level, all levels summing to $\le \alpha$, all bets predictable, stopping by the rule in `certwalk.active` (a stopping time of the joint filtration). Then with probability $\ge 1 - \alpha$, all hold at the final time simultaneously. On that event:

1. $\mathbb E[D] \ge A_{\rm lo}$ and $\Delta_C \in [\Delta_{C,\rm lo}, \Delta_{C,\rm hi}]$ (no further assumption);
2. if also $H_C$ holds for both arms, $\mathbb E[D] \in [A_{\rm lo} + S_{\rm lo} M_{\rm lo},\ A_{\rm hi} + S_{\rm hi} M_{\rm hi}]$ and $\Delta \in [\Delta_{C,\rm lo} + S_{\rm lo}M_{\rm lo} - S_{u,\rm hi}M_{u,\rm hi},\ \Delta_{C,\rm hi} + S_{\rm hi}M_{\rm hi} - S_{u,\rm lo}M_{u,\rm lo}]$.

*Proof.* Theorem 17 with $K = 7 \times$ (biomes $\times$ radii) quantities. 1 is Theorem 18 and the $A$ and $\Delta_C$ sequences. For 2, Theorem 18 and Proposition 19 give $\mathbb E[D] = A + S M$ with all three factors non negative, and $(a, s, m) \mapsto a + s m$ is non decreasing in each on $[0, \infty)^3$, so the box of intervals maps into the stated interval. The same holds for $\Delta = \Delta_C + S M - S_u M_u$, increasing in $S, M$ and decreasing in $S_u, M_u$. $\square$

The radius groups and the two arms run on disjoint chunk folders. The pairing uses only seeds both arms have finished (`certwalk.load_arms`). The stopping rule continues a radius until every target biome has relative half width $\le 5\%$ in *both* arms, or until $n_{\max}$.

### 8.5 Code to model

| code | model | status |
|---|---|---|
| `discexact --origin spawn` | $p(S)$ = `estimateSpawn` | [C] unchanged from section 4 |
| `discexact --origin uniform:L` | $p_u(S)$ uniform on $\{-L..L\}^2$ (blocks) from splitmix of $S \oplus$ a constant | [C] `test_uniform_origin_*` |
| missing row for a biome on a ray | $D > C$ (never reached within the cap) | [P] the C code emits every biome with a finite capped distance (section 6.3), checked by `verify` |
| `walk_terms` | $W_i, K_i, E_i, X_i$ | [C] `test_walk_terms_match_dense` |
| `quantity`, `bias` | Theorem 20 sets | [C] coverage tests in `tests/test_certwalk.py` |

### 8.6 The error budget: code's number vs the model's true $\mathbb E[D]$

The reported range for each biome is the union of four separately stated parts. Only the last involves chance.

| part | size | kind | why |
|---|---|---|---|
| geometry (code vs model) | 0 | hard, 100% | sections 4 and 6.3: every cell is checked (stride 1), no sparse grid; `verify` re-derives random production rays |
| rounding | $\le 0.5$ blocks | hard, 100% | Proposition 12: each stored distance is $\lfloor D + \frac12 \rfloor$, so $\lvert \text{stored} - D\rvert \le \frac12$, and $\min(\cdot, C)$ is 1 Lipschitz |
| discretisation | 0 | hard, 100% | the model is defined on the game's 4x4 biome cells (section 1.2); there is nothing finer to converge to |
| cap, lower side | 0 | hard, 100% | Theorem 18: $\mathbb E[D] \ge A_C$ |
| cap, upper side (tail) | $S_C T_C$, reported as a share | assumption $H_C$ | a finite simulation cannot bound what happens past $C$; the share is planned $\le 5\%$ |
| seed sampling | $\pm\varepsilon_{\rm MC}$ | random, failure chance $\delta$ | Theorem 20; no finite $N$ method that samples seeds has a deterministic bound (only enumerating all $2^{64}$ seeds would) |

**Proposition 21 [P] (rounding folds into the interval).** If every stored distance $\tilde D$ satisfies $\lvert \tilde D - D \rvert \le \frac12$, then $\lvert \mathbb E\min(\tilde D, C) - \mathbb E \min(D, C)\rvert \le \frac12$, $P(\tilde D > C)$ and $P(D > C)$ differ only by the mass of $D \in (C - \frac12, C + \frac12]$, and the reported interval widened by $\frac12 + C\cdot P(\lvert D - C\rvert \le \frac12)$ on each side contains the unrounded quantity. *Proof.* 1 Lipschitz property of $\min(\cdot, C)$, and $\mathbf 1\{\tilde D > C\} \neq \mathbf 1\{D > C\}$ only if $\lvert D - C \rvert \le \frac12$. $\square$ The second term is below $10^{-4}$ relative for every target (the density of $D$ at $C$ is at most $1/\mathbb E[D]$ scale), and the report adds the $\frac12$ block explicitly.

Each number is reported as $\hat\mu\ \pm\ \varepsilon$ with $\varepsilon = \max(\hat\mu - \ell, u - \hat\mu)$, plus the tail share and the stated $\delta$. Two biomes are **ordered** only if their ranges do not overlap; otherwise they are reported as **tied**.

### 8.7 Early stop and one pass for all radii (exact)

`discexact --stopset B` scans each ray in segments of 1,024 blocks by the cell centre projection $t_c = \langle c - p, u\rangle$ and drops a radius as soon as it cannot change any answer for the biomes in $B$.

**Lemma 22a [P].** For every cell $Q$ with centre $c$ and every $r \ge 0$, $D(Q, r) \ge t_c - 2\sqrt2$.

*Proof.* Every $y \in Q$ has $\lvert\langle y - c, u\rangle\rvert \le 2\sqrt 2$ (half diagonal). If $D = \operatorname{dist}(p, Q) \le r$, then $D = \lvert y^* - p\rvert \ge \langle y^* - p, u\rangle \ge t_c - 2\sqrt2$ for the nearest $y^*$. Otherwise $D = s + r$ with $\lvert p + s u - y\rvert \le r$ for some $y \in Q$, so $s \ge \langle y - p, u\rangle - r \ge t_c - 2\sqrt 2 - r$ and $D \ge t_c - 2\sqrt 2$. $\square$ Test: `test_lemma_cell_D_at_least_centre_projection_minus_2sqrt2`.

**Proposition 22 [P].** After all cells with $t_c < T$ are processed, let $\rho = \min(T - 3, C)$. If $\rho = C$, or every $b \in B$ already has a cell with $D \le \rho$, stop that radius and record $\rho$. Then for every biome $b$ (in $B$ or not), the recorded minimum equals the full scan minimum whenever either is $\le \rho$; and for $b \in B$ a missing row means $D_b > C$.

*Proof.* Unprocessed cells have $t_c \ge T$, so $D \ge T - 2\sqrt2 > \rho$ by Lemma 22a: they cannot lower any minimum that is $\le \rho$. Each processed cell's $D$ is computed from the ray's own origin and the full cap, so processed values equal the full scan's. If the radius stopped with $\rho < C$, every $b \in B$ was found with $D \le \rho$, so a missing $b \in B$ only happens when $\rho = C$, i.e. no cell with $D \le C$ exists. $\square$ Checked on data by `certwalk.check_reach` and by `verify` (a full scan up to the reach). Equality with the full scan: `test_early_stop_rows_equal_full_scan_within_reach` and 22,268 rows on 160 production like rays with 0 mismatches.

So the statistics of section 8.2 computed from the rows are exactly those of the full scan for every biome in $B$, which is every biome seen in the pilot. A biome outside $B$ would only get rows that are exact up to $\rho$; none is reported. All radii run in one pass (the widest still active radius sets the strip), and radii drop out of later chunks by the predictable rule of Theorem 20, so each radius uses a prefix of the seeds.

**Cost (measured on 48 rays, cap 540,000, all three radii):** mean reach 255k / 158k / 138k blocks for $r = 0 / 64 / 128$, 9.1 s per ray on one cloud core, against 20 s for full caps run separately.

## 9. Certifying an order from the paired difference

Section 8 orders two biomes only when their ranges are disjoint. Both biomes are measured on the same seeds and rays, so the difference can be certified directly.

For biomes $a, b$ at radius $r$ with the common cap $C$, $\Delta_{ab} = \mathbb E[D_a] - \mathbb E[D_b] = (A_a - A_b) + S_a T_a - S_b T_b$ (Theorem 18 for each). Per seed, $V_i = W_{a,i} - W_{b,i} + JC \in [0, 2JC]$ and $\mathbb E[V_i]/J = A_a - A_b + C$.

**Theorem 23 [P | A1, A2].** Fix, before seeing production data, a list $\Pi$ of ordered pairs. Give each pair one more confidence sequence (the Corollary of 8.2 on $V_i$ with $R = 2C$), with levels added to the budget of Theorem 20. Then with probability $\ge 1 - \alpha$ all sequences hold at once at the final time, and on that event, for every $(a, b) \in \Pi$:

1. $A_a - A_b \in [\ell_{ab}, u_{ab}]$ with no further assumption, and
2. under $H_C$ for $a$ and $b$, $\Delta_{ab} \ge \ell_{ab} + S_{a,\rm lo}T_{a,\rm lo} - S_{b,\rm hi}T_{b,\rm hi} - 1$ (the $-1$ covers rounding, Proposition 21, $\frac12$ per biome).

So $a$ is certified rarer than $b$ when that lower bound is $> 0$.

*Proof.* Union bound over all sequences (Theorem 17); $V_i$ is bounded in $[0, 2JC]$ and iid across seeds under A1, so the Corollary applies; then $\Delta = (A_a - A_b) + S_aT_a - S_bT_b$ is increasing in $S_a, T_a$ and decreasing in $S_b, T_b$, all non negative. $\square$

**Proposition 24 [P] (it is never wider, and is about half the seeds when the two are uncorrelated).** Let $\sigma_a^2, \sigma_b^2$ be the per seed variances of $W_a, W_b$ and $\varrho$ their correlation. For intervals whose half width is $\kappa z \sigma / \sqrt N$ (Theorem 16's leading term), disjoint intervals need a gap of $\kappa z(\sigma_a + \sigma_b)/\sqrt N$ while the paired sequence needs $\kappa z \sqrt{\sigma_a^2 + \sigma_b^2 - 2\varrho\sigma_a\sigma_b}/\sqrt N$. Since $\varrho \ge -1$, the second is $\le$ the first. For $\sigma_a = \sigma_b$ and $\varrho = 0$ the seeds needed for a given gap fall by the factor $(2/\sqrt 2)^2 = 2$; for $\varrho > 0$ by more.

*Proof.* $\sigma_a^2 + \sigma_b^2 - 2\varrho\sigma_a\sigma_b \le \sigma_a^2 + \sigma_b^2 + 2\sigma_a\sigma_b = (\sigma_a + \sigma_b)^2$. Seeds scale as the square of the required width. $\square$ (The tail terms are not paired, but they are $\le 2\%$ of each number here, so they add little.)

What it cannot do: a true gap of 1% still needs the paired width under 1%, so roughly $(5 / 1)^2 / 2 \approx 12$ times the seeds of a $\pm 5\%$ run for an uncorrelated pair.

### 9.1 In the sampler: every pair, per biome caps (`certwalk.py order`, added 2026-11-23)

**Proposition 28 [P | A1, A2].** Take the family $\Pi$ of *all* unordered pairs of stop set biomes at every radius of the plan, with level $\alpha_{\rm pair} / (|\Pi| \cdot \#\text{radii})$ each. For a pair $(a, b)$ with caps $C_a, C_b$ (8.8), let $V_i = W_{a,i} - W_{b,i} + J C_b \in [0, J(C_a + C_b)]$, so $\mathbb E[V_i]/J = A_a - A_b + C_b$. The bets' constants come from independent exponential worlds with the pilot means (`_pair_prior`, fixed random seed). Then, except with chance at most $\alpha + \alpha_{\rm pair}$, every range of Theorem 20 and every pair bound
$$\Delta_{ab} \in \big[\, \ell_{ab} - C_b + S_{a,\rm lo}T_{a,\rm lo} - S_{b,\rm hi}T_{b,\rm hi} - 1,\ \ u_{ab} - C_b + S_{a,\rm hi}T_{a,\rm hi} - S_{b,\rm lo}T_{b,\rm lo} + 1 \,\big]$$
hold at once, the upper and lower tail terms using $H_C$ exactly as in Theorem 23.

*Proof.* As Theorem 23. $V_i$ is bounded and iid across seeds (A1), so the Corollary of 8.2 applies with $R = C_a + C_b$. The union bound runs over Theorem 20's sequences and the pair sequences. $\square$

**Why choosing it after seeing data is allowed.** The family (all pairs), the levels (an equal split) and the bets (pilot only) do not depend on any production data. So the coverage event for the pair sequences has probability $\ge 1 - \alpha_{\rm pair}$, whenever and for whatever reason the computation is run. Picking only the pairs that *looked* close in the report would not be allowed. That is why every pair is included. *Disclosure:* this was added on 2026-11-23, after the first r = 128/512 report showed large ties. The quoted failure chance for order statements is $\alpha + \alpha_{\rm pair} = 2 \times 10^{-6}$.

**Rank ranges.** Biome $x$ has rank between $1 + \#\{y : y \text{ certified rarer than } x\}$ and $N - \#\{y : y \text{ certified more common}\}$. On the coverage event the true rank lies in that range.

## 10. Skipping cells with a Lipschitz bound: checked, and it does not work with global bounds

Idea: if a cell's climate point is far from every box of a rare biome, nearby cells cannot be that biome either, so their lookups could be skipped. The nearest box distance $\sqrt{d(n, \text{box})}$ is 1 Lipschitz in the climate vector $n$ (each coordinate term $\max(0, lo - n_k, n_k - hi)$ is 1 Lipschitz, and a Euclidean norm of 1 Lipschitz terms is 1 Lipschitz). So if $\sqrt{d_b(n)} - \sqrt{d_{\rm best}(n)} > 2\eta$ and $\lVert n(q') - n(q)\rVert \le \eta$, then $q'$ is not biome $b$, whatever the tie rule (strict inequality) [P], provided the tree search returns a true nearest box [C, to be tested against brute force].

The obstacle is $\eta$. A rigorous bound on how fast the climate changes between cells, from the octave amplitudes and lacunarities of 1.21 (crude gradient bound $8.5\sqrt 2$ per unit for improved Perlin noise, measured on the actual generator), gives:

* the shift noise moves the sampling point by up to 9.7 cells, so two neighbouring cells may sample climate up to about 20 cells apart;
* the resulting bound on the change of continentalness between cells 1 apart is about 4.3, and of weirdness about 5.8, in units where the whole range is about $\pm 1$.

Those bounds are useless: no cell could ever be skipped. The real noise is far smoother than the worst case, but a guarantee must use a provable bound, and the shift noise's high frequency octaves make the global bound loose. A *local* version (interval arithmetic on each octave's actual lattice gradients over a small region, including the shift) might be much tighter. That is a research question, not a known speedup, and the earlier estimate of "5x or more" in chat was not justified.

### 8.8 A cap per biome (added 2026-11-22, before the report)

With one cap $C = 540{,}000$ for every biome, a common biome (say $\mathbb E[D] \approx 1{,}000$) never reaches the far window $[C/2, C]$, so its tail rate has no data and the $H_C$ upper end is $+\infty$, although $S_C$ is tiny. Theorem 18 holds for *any* cap, so each biome may use its own $C_b$.

**Rule.** $C_b = \min\big(C,\ \lceil 4\,\hat\mu_b / 1000 \rceil \cdot 1000\big)$, where $\hat\mu_b$ is the pilot estimate of $\mathbb E[D_b]$ stored in the plan. Bets' prior constants are recomputed from $\hat\mu_b$ and $C_b$ with a fixed random seed.

**Proposition 25 [P | A1, A2].** Theorem 20 holds unchanged with $C_b$ in place of $C$ for every biome.

*Proof.* The rows are exact for every $b$ in the stop set up to $D \le C$ (Proposition 22), hence for every $C_b \le C$. $C_b$ and the bets are functions of the pilot only, which is independent of the production seeds (A1), so conditionally on the pilot every sequence is a valid betting sequence (Theorem 16 and the Corollary of 8.2). The number of sequences and their levels are unchanged. Validity at any stopping time does not depend on which rule stopped the run. $\square$

*Disclosure.* This rule was added after a progress check showed infinite upper ends for common biomes. The rule uses no production data and the same $4\times$ multiplier as the global cap, so the guarantee is unaffected. Every biome now has a planned tail share of about $e^{-4} \approx 1.8\%$.

### 8.9 All layers of the column: cave biomes included (added 2026-11-22)

**Model change.** The surface map $\beta_S$ of section 1.1 is replaced by the *column map*
$$\beta^{\mathrm{col}}_S(q) = \{\, \mathrm{biome}_S(q, y) : y = -16, \dots, 79 \,\} \subseteq \mathcal B,$$
the set of biomes over all 96 quart layers of the cell (world $y = -64$ to $319$), where $\mathrm{biome}_S(q, y)$ is Cubiomes' `sampleBiomeNoise` at $(q_x, y, q_z)$ followed by the hint free `climateToBiome`, that is, the game's stored biome of that 4x4x4 cell. Biome $b$ occupies the cells $A_b = \{q : b \in \beta^{\mathrm{col}}_S(q)\}$ and everything else (the discovery functional of 1.2, $D_b = D(A_b, r)$, sections 8.1 to 8.8) is unchanged. So a cave biome counts as found when the walker comes within $r$ of the column above or below it, at any depth, and a surface biome is found at least as early as before ($A_b^{\mathrm{surf}} \subseteq A_b$ up to the surface reconstruction, checked by `test_column_superset_of_surface_and_caves_found`). The old surface only model is kept as `--layers surface`; certificates from it (the r = 0 run of 2026-11-22) are about the surface model only.

**Assumption audit.** "Present anywhere in the column" is a modelling choice (section 0.2, biome layer): it does not ask whether the cave is open, reachable or visible.

Write $x_i \in \mathbb Z^6$ for the climate vector at layer $i$. Only the depth $x_{i,4}$ depends on the layer: Cubiomes samples the other five noises at $y = 0$, and the depth is the float $d_i = 1 - 4y/128 - 83/160 + \mathrm{off}$ with the spline offset off fixed per cell, so `fast_np_column` computes the five values and off once and `fast_depth_at` reproduces $x_{i,4}$ with the same operations, bit for bit.

The tree search returns a leaf $\ell$ of the 1.21 table. A leaf has a box $\prod_k [a_k, b_k]$ and cost $c(\ell, x) = \sum_k \phi(x_k; a_k, b_k)$ with $\phi(t; a, b) = \max(t - b, a - t, 0)^2$ in exact unsigned 64 bit arithmetic (no overflow: each term is below $2^{31}$).

**Lemma 26a [P + C].** For every $x$, `climateToBiome(x, NULL)` returns the biome of the first leaf, in the search's traversal order, among the leaves of least cost.

*Proof.* Every non-root node's box contains the boxes of its children [C: `test_tree_facts`, all 9,105 parent and child pairs below the root], so a node's cost lower-bounds every leaf below it. By induction on the recursion of `get_resulting_node`: given a current best $(\ell^*, d^*)$, a child subtree is entered only if its bound is $< d^*$, a subtree with bound $\ge d^*$ holds no leaf of cost $< d^*$, and a leaf replaces $\ell^*$ only if its cost is strictly smaller. So after the children are scanned, $\ell^*$ is the first leaf in traversal order of least cost among those seen, and no unseen leaf is cheaper. Starting from $d^* = 2^{64} - 1$ gives the claim. $\square$

**Proposition 26 [P + C] (the class split is exact).** Partition the leaves by their depth interval $[a_4, b_4]$ (classes $K$; in 1.21 there are four: $[0,0]$, $[0.2, 0.9]$, $[1,1]$, $[1.1, 1.1]$ in units of $10^4$ [C]). Let $c_5(\ell) = \sum_{k \ne 4} \phi(x_k; a_k, b_k)$, which does not depend on the layer, and let $w_K$ be the first leaf of class $K$ in traversal order with least $c_5$. Then at every layer $i$ the search's leaf is the first in traversal order among $\{w_K\}$ of least $c_5(w_K) + \phi(x_{i,4}; K)$.

*Proof.* Let $M$ be the set of least cost leaves at layer $i$ and $\ell^*$ its first element (Lemma 26a). Let $K$ be the class of $\ell^*$. Within $K$ the depth term is the same for all leaves, so $\ell^*$ has least $c_5$ in $K$. Any $\ell \in K$ with the same $c_5$ has the same cost and is in $M$, so it comes after $\ell^*$. Hence $\ell^* = w_K$. Every other $w_{K'}$ costs at least as much, and one that costs the same is in $M$ and comes after $\ell^*$. So the rule picks $\ell^*$. $\square$

**How $w_K$ is found [P + C].**
* Classes with at most 4 leaves (the two cave classes): direct enumeration in traversal order with strict improvement.
* A large class: the same branch and bound with cost $c_5$, entering a child only if its depth box contains the class interval, since a subtree without that can hold no leaf of the class (nested boxes). The strict improvement argument of Lemma 26a gives $w_K$.
* **Lemma 26b.** The classes $[0,0]$ and $[1,1]$ pair up leaf by leaf, with the same biome and the same other five intervals, and these boxes are pairwise distinct [C: `test_tree_facts`]. The search over $[0,0]$ also explores subtrees with bound equal to the best and flags a second leaf of equal least $c_5$. If there is no tie, the least $c_5$ in $[1,1]$ is attained only at the partner of $w_{[0,0]}$, so $w_{[1,1]}$ is that partner. If there is a tie, $[1,1]$ is searched separately.

**Check against brute force [C].** `--column-check` compares the class split with all 96 layers through Cubiomes' own functions: 0 mismatches on 96,000 random cells (`test_column_check_brute_force`, cells far out and near spawn). The fast build and the `-DDISCEXACT_REFERENCE` build (brute force column) give byte-identical CSV with early stop on (`test_fast_equals_reference`). `certwalk.py verify` reruns production rays through `--debug`, which uses the brute force column. So the full scan check of 8.7 also checks the class split on production rays.

**Early stop (8.7) and the error budget (8.6) are unchanged.** Lemma 22a and Proposition 22 only use that each cell contributes its biomes at its exact $D_c$. A cell now contributes a set of biomes at the same $D_c$, and the stop set rule and the reach row are per biome. Rounding, geometry and the tail are as before.

**Cost.** 1.27x the surface only scan on the same rays (3.84 s vs 3.02 s for 4 seeds x 4 rays, radii 0, 64, 128, cap 20,000, 4 cloud threads). One noise sample per cell, as before, plus a filtered search and 96 x 4 additions.

### 8.10 Continuing a finished run (`run --until N`)

A run stops by itself once every target biome meets its precision. `certwalk.py run --until N` keeps every radius still in the last chunk going until it has $\min(N, n^{\max}_r)$ seeds, met target or not.

**Proposition 27 [P | A1, A2].** The guarantee of Theorem 20 holds for the report made after any such continuation, at the same failure chance $\delta$, for any number of continuations decided after looking at earlier reports.

*Proof.* The sequences are confidence sequences, so they cover at every stopping time at once (Theorem 20). The decision to continue, and where to stop, is a function of chunks already finished, so the final seed count is a stopping time. The seeds stay a prefix of the planned seed order: chunk $k$ always uses seeds $s_0 + k \cdot \text{chunk}$ onward. And $n^{\max}_r$ comes from the hashed plan, so the reserved seed range in the ledger is not exceeded. No new sequence is opened, so $\delta$ is unchanged. $\square$

A radius that the stopping rule already dropped is not revived. Its seeds would no longer be a prefix.

**Proposition 27b [P | A1, A2] (past $n^{\max}$, spawn arm only, `run --until N --extend-spawn`).** The guarantee of Theorem 20 and of Proposition 28 still holds, at the same $\delta$ and $\alpha_{\text{pair}}$, when the spawn arm continues to any $N > n^{\max}_r$, provided the seed indices $[s_0 + n^{\max}, s_0 + N)$ are checked against the ledger and reserved there before any of them is simulated. The uniform arm stops at $n^{\max}_r$. Its quantities, and the spawn bias $\Delta$ (8.3), are then computed on the first $n_u = n^{\max}_r$ seeds that both arms share.

*Proof.* Theorem 16 has no horizon: $n^\star$ only tunes the bets, and coverage holds at every $n$ at once. $n^{\max}$ enters the guarantee only through the ledger, which keeps the production seeds disjoint from the pilot and from every other run (A1). The reservation keeps that true for the new range. The new seeds are the next indices of the same prefix, so every sequence of the plan simply runs on. The spawn arm's sequences are read at its own stopping time $N$. The uniform arm's and the paired bias sequences are read at their stopping time $n_u$. A confidence sequence covers at every stopping time, and the union bound of Theorem 20 is over sequences, not times, so reading different sequences at different times keeps $\delta$. No new sequence is opened. $\square$

*Disclosure.* Added 2026-11-22 after the 53,750 seed report, to split middle ties at $r = 0$. The decision to extend looked at the results, which Proposition 27's argument allows.

### 8.11 A spawn effect that does not depend on area or clumping (`spawnratio.py`, added 2026-11-22)

The bias $\Delta = \mathbb E[D] - \mathbb E[D_u]$ of 8.3 is in blocks. Dividing it by $\mathbb E[D_u]$ makes common biomes look strongly affected, because their whole walk fits in the stretch near spawn. Also, for a rare biome $\Delta$ is roughly the size of the spawn zone times how much spawn favours the biome (Remark below), not a fraction of the walk. So we compare the two starts *at the same distance* instead.

**Definition.** For biome $b$ at radius $r = 0$ and distance $x \ge 0$, let $F(x) = P(D \le x)$ (start at spawn) and $F_u(x) = P(D_u \le x)$ (uniform start, 8.3). The **spawn likelihood ratio** is
$$ \rho_b(x) = \frac{F(x)}{F_u(x)} \quad (F_u(x) > 0). $$
$\rho_b(x) > 1$ means a player starting at spawn is more likely to have found $b$ within $x$ blocks than one starting at a random place.

**Proposition 29 [P] (area cancels exactly at $x = 0$).** At $r = 0$, $F_u(0) = a_b$, the fraction of cells of $[-L, L]^2$ whose column contains $b$, and $F(0) = P(\text{the spawn column contains } b)$. Hence
$$ \rho_b(0) = \frac{P(\text{spawn column contains } b)}{a_b}. $$

*Proof.* With $r = 0$, $D = 0$ exactly when the start cell's column contains $b$ (section 1.2 and 8.9: the found set at distance 0 is the start column). For the uniform start, the start cell is uniform on the cells of $[-L, L]^2$, independent of the map given the seed, so $P(D_u = 0 \mid \text{seed}) $ is the fraction of those cells containing $b$. Average over seeds. $\square$

So $\rho_b(0)$ is "how many times more (or less) likely the spawn spot is to be in $b$ than a random spot". The area of $b$ is divided out exactly. Clumping does not enter, because a single point has no neighbourhood. This is the headline spawn effect.

**Interpretation for $x > 0$ [E].** $F_u(x)$ is the chance for a walk of length $x$ through the same terrain law from a random start, so it already contains the area and the clumping of $b$ at that scale. $\rho_b(x)$ then shows how far spawn's pull reaches: $\rho_b(x) \to 1$ as $x$ grows, once the walk has left the region that spawn selection shaped. That it removes clumping *exactly* is not claimed for $x > 0$. It is shown as a curve, not as a ranking.

**Remark [A] (why blocks were already fair for rare biomes).** Suppose spawn changes the hazard only on $[0, R]$, and after that both walks have the same constant hazard $h$. Then
$$ \Delta = \int_0^R (F_u - F)\,dx + \frac{F_u(R) - F(R)}{h}. $$
For a rare biome, $hR \ll 1$, and $F(R) \approx \bar\rho\, hR$ and $F_u(R) \approx hR$, so $\Delta \approx R(1 - \bar\rho)$, with $\bar\rho$ the average ratio over $[0, R]$. This does not depend on $h$, so it does not depend on area. For a common biome $hR \gg 1$, so $|\Delta| \le \mathbb E[D_u]$ is small in blocks. The percent hides this.

**Bounds [P | A1, A2].** Fix the grid $x_1 < \dots < x_K \le C$ (all below the simulation cap, where the rows are exact, Proposition 22). Per seed $i$, $Y_i(x) = \#\{j : D_{ij} \le x\} \in [0, J]$, so $\mathbb E[Y_i(x)]/J = F(x)$. The Corollary of 8.2 with $E_i \equiv J$, $R_0 = 0$, $R = 1$ gives an anytime valid confidence sequence for $F(x)$ at level $\alpha_\rho/(2BK)$, and the same for $F_u(x)$ from the uniform arm, for each of $B$ biomes. By the union bound, except with chance at most $\alpha_\rho$, all $2BK$ intervals $[\ell, u]$ hold at once. On that event,
$$ \rho_b(x) \in \Big[\frac{\ell(x)}{u_u(x)},\ \frac{u(x)}{\ell_u(x)}\Big] $$
for every $b$ and $x$, since $F/F_u$ increases in $F$ and decreases in $F_u$. The upper end is $+\infty$ when $\ell_u = 0$. As in Proposition 27, this holds at the final seed count even though that count was chosen after looking at the data. "Spawn favours $b$" is certified when the lower end is $> 1$, and "avoids" when the upper end is $< 1$.

*Proof.* Each sequence is a valid betting sequence (the bets use only earlier seeds and constants from a pilot on other seeds), so Theorem 16 and the Corollary give coverage at every stopping time. The union bound adds the $2BK$ failure chances. Monotonicity gives the ratio bounds. $\square$

The default is $\alpha_\rho = 10^{-6}$, separate from the $\alpha$ of the E[D] report. Anyone who wants every statement of both reports at once adds the two failure chances.
