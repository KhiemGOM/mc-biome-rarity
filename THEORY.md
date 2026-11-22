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

## 1. The mathematical model

### 1.1 Population and randomness

* $\mathcal S = \{0,1\}^{64}$ is the set of world seeds. $S$ is uniform on $\mathcal S$.
* For each seed, $p(S) \in \mathbb Z^2$ is the spawn point and $\beta_S : \mathbb Z^2 \to \mathcal B$ is the surface biome of each 4x4 cell $q = (q_x, q_z)$. Both are deterministic functions of $S$ (they are *defined* as the Cubiomes functions named in section 4, so there is no approximation at this step).
* $U \sim \mathrm{Unif}[0,1)$ independent of $S$. A seed is explored along $J = 4$ rays with angles $\theta_j = 2\pi (j + U)/J$, $j = 0, \dots, J-1$, direction $u_j = (\cos\theta_j, \sin\theta_j)$. Each $\theta_j$ is marginally uniform on $[0, 2\pi)$ and independent of $S$; the $J$ rays of one seed are dependent (same map), which is why the seed, not the ray, is the sampling unit.

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

$$ M = \frac{\mathbb E[X]}{\mathbb E[E]} = \frac{\mathbb E[x(D)]}{\mathbb E[e(D)]} \quad\text{(one ray, by identical marginals)}, $$

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
| `certrun.py` intervals all hold at once with prob $\ge 1-\alpha$ at the planned N | [P \| A1, A2] Theorem 13 |
| `certrun.py` computes those intervals from exactly the planned seeds and the exact model | [P] + [C] section 6.3, re-checked by `verify` |

## 6. The certified sampler (`certrun.py`)

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
