"""
URL dataset domain constraints (CAA / constrained-attacks setting).

All feature indices are 0-based and match the column order of
``data/url_features.csv`` (63 features, same order as ``data/url.csv``).

Two kinds of constraints are implemented, evaluated in the RAW feature space:

* per-feature boundaries (min/max from url_features.csv) + type rounding
  (int features must be integers) -- "boundary / type" constraints;
* the 14 relation/linear constraints g1..g16 (authoritative set from
  ``data/url_constraints_reference.py``; g7/g9 are commented out there and
  are NOT part of the set).

Both a *penalty* formulation (used inside the CPGD/CAPGD objective
L' = l(h(x), y) - sum_penalty, Eq. (4) of the paper) and a *repair*
operator R_Omega (used by CAPGD Algorithm 1) are provided.

All heavy computations are vectorized with torch so the attacks can be
run in batches over many samples at once.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import torch

_FEATURES_CSV_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "url_features.csv"
)

# 0-based feature indices (column order of url_features.csv == url.csv columns)
FEATURES = [
    "length_url", "length_hostname", "ip", "nb_dots", "nb_hyphens", "nb_at",
    "nb_qm", "nb_and", "nb_or", "nb_eq", "nb_underscore", "nb_tilde",
    "nb_percent", "nb_slash", "nb_star", "nb_colon", "nb_comma",
    "nb_semicolumn", "nb_dollar", "nb_space", "nb_www", "nb_com",
    "nb_dslash", "http_in_path", "https_token", "ratio_digits_url",
    "ratio_digits_host", "punycode", "port", "tld_in_path",
    "tld_in_subdomain", "abnormal_subdomain", "nb_subdomains",
    "prefix_suffix", "random_domain", "shortening_service",
    "path_extension", "nb_redirection", "nb_external_redirection",
    "length_words_raw", "char_repeat", "shortest_words_raw",
    "shortest_word_host", "shortest_word_path", "longest_words_raw",
    "longest_word_host", "longest_word_path", "avg_words_raw",
    "avg_word_host", "avg_word_path", "phish_hints", "domain_in_brand",
    "brand_in_subdomain", "brand_in_path", "suspecious_tld",
    "statistical_report", "whois_registered_domain",
    "domain_registration_length", "domain_age", "web_traffic",
    "dns_record", "google_index", "page_rank",
]


def _idx(name: str) -> int:
    return FEATURES.index(name)


class URLConstraintSet:
    """Boundary + type + relation constraints for the URL dataset."""

    def __init__(self, features_csv: str = None, eps_a: float = 1e-9, delta_real: float = 1e-4):
        if features_csv is None:
            features_csv = _FEATURES_CSV_DEFAULT
        meta = pd.read_csv(features_csv)
        assert list(meta["feature"]) == FEATURES, "feature order mismatch"
        self.d_min = torch.tensor(meta["min"].to_numpy().astype(np.float64))
        self.d_max = torch.tensor(meta["max"].to_numpy().astype(np.float64))
        self.is_int = torch.tensor((meta["type"] == "int").to_numpy())
        self.int_idx = torch.nonzero(self.is_int).flatten().tolist()

        # minimum allowed positive value for the right-hand side of the
        # "if a>0 then b>0" constraints (minimal repair keeps the sample
        # as close as possible to the pre-repair point inside the eps-ball).
        delta = torch.full((len(FEATURES),), float(delta_real))
        for i in self.int_idx:
            delta[i] = 1.0
        self.delta = delta
        self.eps_a = eps_a

        self._build_linear()
        self._build_implications()

    # ------------------------------------------------------------------ #
    # constraint definitions (indices follow url_constraints_reference.py)
    # ------------------------------------------------------------------ #
    def _build_linear(self):
        """Linear inequalities c @ x <= c0, expressed in RAW space."""
        F = len(FEATURES)
        lin = []  # (c vector, c0)
        c = np.zeros(F)
        c[_idx("length_hostname")] = 1.0          # g1: length_hostname <= length_url
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 0.0))

        c = np.zeros(F)                            # g2: sum(x3..x17) + 3*x19 <= x0
        for i in range(3, 18):
            c[i] = 1.0
        c[_idx("nb_space")] = 3.0
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 0.0))

        c = np.zeros(F)                            # g5: 3*x20 + 4*x21 + 2*x23 <= x0
        c[_idx("nb_www")] = 3.0
        c[_idx("nb_com")] = 4.0
        c[_idx("http_in_path")] = 2.0
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 0.0))

        c = np.zeros(F)                            # g12: x38 <= x37
        c[_idx("nb_external_redirection")] = 1.0
        c[_idx("nb_redirection")] = -1.0
        lin.append((c.copy(), 0.0))

        c = np.zeros(F)                            # g13: 3*x20 <= x0 + 1
        c[_idx("nb_www")] = 3.0
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 1.0))

        c = np.zeros(F)                            # g14: 4*x21 <= x0 + 1
        c[_idx("nb_com")] = 4.0
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 1.0))

        c = np.zeros(F)                            # g15: 4*x2 <= x0 + 1
        c[_idx("ip")] = 4.0
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 1.0))

        c = np.zeros(F)                            # g16: 2*x23 <= x0 + 1
        c[_idx("http_in_path")] = 2.0
        c[_idx("length_url")] = -1.0
        lin.append((c.copy(), 1.0))

        self.lin_c = torch.tensor(np.stack([c for c, _ in lin])).to(torch.float64)
        self.lin_c0 = torch.tensor([c0 for _, c0 in lin]).to(torch.float64)
        self.lin_norm2 = (self.lin_c ** 2).sum(dim=1)

    def _build_implications(self):
        """if x[a] > 0 then x[b] > 0  (non-convex constraints)."""
        self.imp_a = torch.tensor([
            _idx("nb_com"), _idx("http_in_path"), _idx("nb_space"),
            _idx("ip"), _idx("port"), _idx("abnormal_subdomain"),
        ])  # g3, g4, g6, g8, g10, g11
        self.imp_b = torch.tensor([
            _idx("nb_dots"), _idx("nb_slash"), _idx("ratio_digits_url"),
            _idx("ratio_digits_url"), _idx("ratio_digits_url"),
            _idx("ratio_digits_host"),
        ])
        # names for reporting (index order is authoritative)
        self._imp_names = [
            ("nb_com", "nb_dots"), ("http_in_path", "nb_slash"),
            ("nb_space", "ratio_digits_url"), ("ip", "ratio_digits_url"),
            ("port", "ratio_digits_url"),
            ("abnormal_subdomain", "ratio_digits_host"),
        ]

    # ------------------------------------------------------------------ #
    # feasibility / penalties (raw space, torch)
    # ------------------------------------------------------------------ #
    def boundary_penalty(self, x):
        p = torch.clamp(self.d_min - x, min=0.0) + torch.clamp(x - self.d_max, min=0.0)
        return p.sum(-1)

    def int_penalty(self, x):
        if self.int_idx:
            x_i = x[..., self.int_idx]
            return torch.abs(x_i - torch.round(x_i)).sum(-1)
        return torch.zeros_like(x[..., 0])

    def linear_penalty(self, x):
        val = torch.einsum("...f,kf->...k", x, self.lin_c) - self.lin_c0
        return torch.clamp(val, min=0.0).sum(-1)

    def implication_penalty(self, x):
        a = x[..., self.imp_a]
        b = x[..., self.imp_b]
        delta = self.delta[self.imp_b]
        violated = (a > self.eps_a) & (b <= 0.0)
        cost_b = torch.clamp(delta - b, min=0.0)
        return torch.where(violated, torch.minimum(a, cost_b), torch.zeros_like(a)).sum(-1)

    def total_penalty(self, x):
        """Sum of all constraint penalties  sum_w penalty(x, w)."""
        return (
            self.boundary_penalty(x)
            + 3.0 * self.int_penalty(x)          # small weight: type repair is binary anyway
            + self.linear_penalty(x)
            + self.implication_penalty(x)
        )

    def is_feasible(self, x):
        """Elementwise feasibility check (raw space) -> bool tensor [B].

        Uses a small tolerance (1e-6) to absorb float round-trip noise; the
        constraints themselves are strict on the raw feature values.
        """
        tol = 1e-6
        ok_boundary = ((x >= self.d_min - tol) & (x <= self.d_max + tol)).all(-1)
        ok_int = True
        if self.int_idx:
            x_i = x[..., self.int_idx]
            ok_int = (torch.abs(x_i - torch.round(x_i)) < 1e-6).all(-1)
        ok_linear = (torch.einsum("...f,kf->...k", x, self.lin_c) - self.lin_c0 <= tol).all(-1)
        a = x[..., self.imp_a]
        b = x[..., self.imp_b]
        ok_imp = ((a <= tol) | (b > -tol)).all(-1)
        return ok_boundary & ok_int & ok_linear & ok_imp

    # ------------------------------------------------------------------ #
    # repair operator R_Omega (raw space -> feasible set)
    # ------------------------------------------------------------------ #
    def repair(self, x, n_passes: int = 3, round_int: bool = False):
        """Project/repair an (infeasible) raw-space tensor into the feasible
        set Omega by cycling through box clip + (optional) type rounding +
        half-space projections + implication repairs until convergence.

        ``round_int=False`` during the gradient iterations (integer rounding
        would erase small gradient moves); the FINAL output is produced with
        ``round_int=True`` so the reported examples are valid (integer-typed)
        inputs. The end-to-end postprocessing then re-projects to restore
        feasibility after the rounding.
        """
        x = torch.clamp(x, self.d_min, self.d_max)
        for _ in range(n_passes):
            # type: round integer features (raw space) -- optional
            if round_int and self.int_idx:
                xr = x.clone()
                xr[..., self.int_idx] = torch.round(xr[..., self.int_idx])
                x = xr
            x = torch.clamp(x, self.d_min, self.d_max)
            # linear half-space projections
            for k in range(len(self.lin_c)):
                ck, c0k, n2k = self.lin_c[k], self.lin_c0[k], self.lin_norm2[k]
                val = torch.einsum("...f,f->...", x, ck) - c0k
                alpha = torch.clamp(val, min=0.0) / n2k
                x = x - alpha.unsqueeze(-1) * ck
            # implication repairs (minimal positive value), each applied to a
            # unique feature index (imp_b has repetitions, e.g. three
            # implications share ratio_digits_url)
            x = x.clone()
            for ai, bi in zip(self.imp_a.tolist(), self.imp_b.tolist()):
                need = (x[..., ai] > self.eps_a) & (x[..., bi] < self.delta[bi])
                b_cur = x[..., bi]
                b_new = torch.where(
                    need, torch.clamp(b_cur, min=0.0) + self.delta[bi], b_cur)
                x = x.clone()
                x[..., bi] = b_new
            x = torch.clamp(x, self.d_min, self.d_max)
        # ---- exact integer-aware fixes for the final (rounded) output -------
        # Integer rounding can over-shoot the linear constraints. Step 1: make
        # every int-typed feature integral again (last pass projections leave
        # fractions); Step 2: repair each violated linear constraint with a
        # minimal integer adjustment on the feature that can absorb the
        # deficit (length_url for all count-sum <= url constraints; lower the
        # external redirection count for g12) -- these cannot violate others;
        # Step 3: re-apply implication repairs that rounding may have broken.
        if round_int:
            x = self._finalize_integer(x)
        return x

    def _finalize_integer(self, x):
        x = torch.clamp(x, self.d_min, self.d_max)
        if self.int_idx:
            xr = x.clone()
            xr[..., self.int_idx] = torch.round(xr[..., self.int_idx])
            x = xr
        x = torch.clamp(x, self.d_min, self.d_max)
        self._integer_linear_fix(x)
        # implication repairs on the integral values
        x = x.clone()
        for ai, bi in zip(self.imp_a.tolist(), self.imp_b.tolist()):
            need = (x[..., ai] > self.eps_a) & (x[..., bi] < self.delta[bi])
            b_cur = x[..., bi]
            b_new = torch.where(
                need, torch.clamp(b_cur, min=0.0) + self.delta[bi], b_cur)
            x = x.clone()
            x[..., bi] = b_new
        return torch.clamp(x, self.d_min, self.d_max)

    def _integer_linear_fix(self, x):
        """Exact integer repair of the 8 linear constraints on a rounded x
        (in-place, torch). Assumes integer values on int-typed features."""
        url = 0
        for _ in range(3):  # a couple of sweeps until stable
            # g1, g2, g5, g13, g14, g15, g16 -> absorb deficit in length_url
            for k in (0, 1, 2, 4, 5, 6, 7):
                ck = self.lin_c[k]
                val = torch.einsum("...f,f->...", x, ck) - self.lin_c0[k]
                deficit = torch.ceil(val).clamp(min=0.0)
                room = (self.d_max[url] - x[..., url]).clamp(min=0.0)
                add = torch.minimum(deficit, room)
                x[..., url] = x[..., url] + add
            # g12: nb_external_redirection <= nb_redirection
            ext, red = 38, 37
            viol = x[..., ext] > x[..., red]
            x[..., ext] = torch.where(viol, x[..., red], x[..., ext])
            x.clamp_(self.d_min, self.d_max)


def standard_scaler(raw, mean, std, eps=1e-12):
    return (raw - mean) / torch.clamp(std, min=eps)


def inv_standard_scaler(z, mean, std, eps=1e-12):
    return z * torch.clamp(std, min=eps) + mean