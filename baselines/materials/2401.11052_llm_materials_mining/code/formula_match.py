"""Local approximation of the paper's "formula matching" for material entities.

The original pipeline calls a Grobid *supercon material parser* webservice
(``MaterialParsersClient``) to turn a material string into a list of
compositions -- dicts ``{element: count}`` ("formulaComposition") or names.
Offline, we provide a deterministic rule-based chemical-formula parser that
yields the same *kind* of representation (lists of composition dicts), plus
a dictionary of common superconductor aliases (LSCO, YBCO, Hg-1201, ...).

Matching semantics replicate ``commons.evaluation.match_by_formula``:
  * if the strings are equal ignoring case and spaces -> match;
  * otherwise compare every (expected-composition, predicted-composition)
    pair; dicts match when every element of the expected composition is
    present in the predicted composition with the same count
    (``compare_compositions``); strings match on equality.

This is an intentionally transparent surrogate: exact parity with the
proprietary Grobid service is not guaranteed (see report.md, limitations).
"""
import re

# ---- normalisation ---------------------------------------------------------
SUBSCRIPT_MAP = {o: str(i) for i, o in enumerate("₀₁₂₃₄₅₆₇₈₉")}
GREEK = {"δ": "d", "Δ": "D", "α": "a", "β": "b", "γ": "g", "λ": "l", "μ": "m",
         "µ": "u", "θ": "theta", "σ": "s", "ψ": "psi", "ρ": "rho", "τ": "t",
         "χ": "chi", "ɵ": "o", "≈": "=", "≤": "<=", "≥": ">="}

ELEMENTS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si",
    "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co",
    "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I",
    "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au",
    "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U",
    "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db",
    "Sg", "Bh", "Hs", "Bh", "Ds", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv",
    "Lw", "Uue",
}
# letters that are NOT element symbols and appear as generic variables
VARIABLES = set("XxRrDdTtMmLlGgEeQqZz")

# common superconductor aliases -> formula string
ALIASES = {
    "YBCO": "YBa2Cu3O7",
    "Y123": "YBa2Cu3O7",
    "Y-123": "YBa2Cu3O7",
    "YBCO-123": "YBa2Cu3O7",
    "YBaCuO": "YBa2Cu3O7",
    "LSCO": "La2Sr1CuO4",
    "BSLCO": "La2Sr1CuO4",
    "La214": "La2CuO4",
    "Bi2212": "Bi2Sr2Ca1Cu2O8",
    "BSCCO2212": "Bi2Sr2Ca1Cu2O8",
    "B2212": "Bi2Sr2Ca1Cu2O8",
    "Bi-2212": "Bi2Sr2Ca1Cu2O8",
    "Bi2223": "Bi2Sr2Ca2Cu3O10",
    "Bi-2223": "Bi2Sr2Ca2Cu3O10",
    "Bi2221": "Bi2Sr2Ca1Cu2O8",
    "Bi2201": "Bi2Sr2CuO6",
    "Bi-2201": "Bi2Sr2CuO6",
    "B2201": "Bi2Sr2CuO6",
    "Tl2201": "Tl2Ba2CuO6",
    "Tl-2201": "Tl2Ba2CuO6",
    "T1-2201": "Tl2Ba2CuO6",
    "Tl2212": "Tl2Ba2Ca1Cu2O8",
    "Tl-2212": "Tl2Ba2Ca1Cu2O8",
    "T1-2212": "Tl2Ba2Ca1Cu2O8",
    "Tl2223": "Tl2Ba2Ca2Cu3O10",
    "Tl-2223": "Tl2Ba2Ca2Cu3O10",
    "Tl1212": "Tl2Ba2Ca1Cu2O8",
    "Hg1201": "HgBa2CuO4",
    "Hg-1201": "HgBa2CuO4",
    "Hg1223": "HgBa2Ca2Cu3O8",
    "Hg-1223": "HgBa2Ca2Cu3O8",
    "Hg1212": "HgBa2Ca1Cu2O6",
    "Hg-1212": "HgBa2Ca1Cu2O6",
    "PrBCO": "PrBa2Cu3O7",
    "Pr123": "PrBa2Cu3O7",
    "GdBCO": "GdBa2Cu3O7",
    "Gd123": "GdBa2Cu3O7",
    "Gd-123": "GdBa2Cu3O7",
    "Nd123": "NdBa2Cu3O7",
    "Nd-123": "NdBa2Cu3O7",
    "Eu123": "EuBa2Cu3O7",
    "Eu-123": "EuBa2Cu3O7",
    "Sm123": "SmBa2Cu3O7",
    "Y-247": "YBa2Cu4O8",
    "Y124": "YBa2Cu4O8",
    "Y-124": "YBa2Cu4O8",
    "CBCO": "CaBa2Cu3O7",
    "NdBa2Cu3O7": "NdBa2Cu3O7",
}


_ALIAS_KEYS = sorted(ALIASES, key=len, reverse=True)

# generic RE-123 material families (rare earth cuprates)
_RE123 = ("Y Gd Nd Eu Sm Ho Dy Er Tb La Pr Ce Lu Th Ca Sr Ba".split())


def _norm(s):
    out = []
    for ch in s:
        if ch in SUBSCRIPT_MAP:
            out.append(SUBSCRIPT_MAP[ch])
        elif ch in "−–—‐‑":
            out.append("-")
        elif ch in GREEK:
            out.append(GREEK[ch])
        elif ch in "\u00a0\u2009\u200a":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def _contains_formula(s):
    """Heuristic used to pick the segments that look like formulas."""
    # at least one digit bound to an element symbol
    return re.search(r"[A-Z][a-z]?(?:\([^)]*\))?\d", s) is not None


def _parse_count(s, i):
    """Parse an integer/decimal count in string s starting at i; value may be
    a float; returns (value, next_i) or (None, i)."""
    j = i
    while j < len(s) and (s[j].isdigit() or s[j] == "."):
        j += 1
    if j == i:
        return None, i
    try:
        return float(s[i:j]), j
    except ValueError:
        return None, i


def _parse_formula_string(formula):
    """Parse ``formula`` (e.g. "La2-xSrxCuO4", "Bi2Sr2CaCu2O8+d") into dict.

    Groups with parentheses/brackets are expanded; counts are explicit
    ints/floats; variable subscripts (x, y, d, delta-as-d) are ignored.
    """
    formula = formula.replace("−", "-")
    comp = {}
    i, n = 0, len(formula)
    while i < n:
        ch = formula[i]
        if ch in "([":
            close = formula.find(")" if ch == "(" else "]", i)
            if close == -1:
                break
            inner = formula[i + 1:close]
            grp_mult, k = _parse_count(formula, close + 1)
            grp_mult = grp_mult if grp_mult else 1.0
            inner_comp = _parse_formula_string(inner)
            for el, c in inner_comp.items():
                comp[el] = comp.get(el, 0.0) + c * grp_mult
            i = k
            continue
        if ch.isupper():
            if i + 1 < n and formula[i + 1].islower():
                el = formula[i:i + 2]
                i += 2
            else:
                el = ch
                i += 1
            if el not in ELEMENTS and el not in VARIABLES:
                continue  # not a real element / generic-variable symbol
            cnt, k = _parse_count(formula, i)
            if cnt is None:
                cnt = 1.0
            else:
                i = k
                # swallow a variable suffix like "-d", "+x" after a count
                nxt = i
                while nxt < len(formula) and formula[nxt] in "-+*":
                    nxt += 1
                if nxt < len(formula) and (formula[nxt].islower() or formula[nxt] in VARIABLES):
                    i = nxt + 1
            if el in VARIABLES:
                continue
            comp[el] = comp.get(el, 0.0) + cnt
            continue
        i += 1
    return comp


def parse_material(s):
    """Return list of composition-dicts for a material entity string."""
    s_norm = _norm(s)
    comps = []

    # 1) alias substitution (whole-token matches)
    s_low = s_norm
    for key in _ALIAS_KEYS:
        k = key
        # match as a token delimited by non-alnum
        pattern = r"(?<![A-Za-z0-9])" + re.escape(k) + r"(?![A-Za-z0-9-])"
        s_low = re.sub(pattern, lambda m, orig=k: " " + ALIASES[orig] + " ", s_low, count=50)

    # 1b) generic RE-123 / RE-124 / RE-247 / -1201 style aliases
    def _generic_alias(mo):
        re_el = mo.group(1)
        num = mo.group(2)
        if re_el in _RE123:
            if num == "123":
                return f"{re_el}Ba2Cu3O7"
            if num in ("124", "247"):
                return f"{re_el}Ba2Cu4O8"
            if num == "1201":
                return f"{re_el}Ba2CuO6"
        return mo.group(0)

    s_low = re.sub(r"(?<![A-Za-z0-9])([A-Z][a-z]?)-?(123|124|247|1201)(?![0-9])",
                   _generic_alias, s_low)

    # 2) extract formula-like runs (internal whitespace allowed)
    for token in _scan_formula_runs(s_low):
        # compact the whitespace that separates element symbols from counts
        c = _parse_formula_string(re.sub(r"\s+", "", token))
        if c and all(v is not None and v > 0 for v in c.values()):
            comps.append({el: round(v, 4) for el, v in c.items()})

    uniq = []
    seen = set()
    for c in comps:
        key = tuple(sorted(c.items()))
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


_TOK = r"[A-Z][a-z]?\d*(?:\.\d+)?"
_GRP = r"[\(\[]\s*[^()\[\]\n]{0,80}\s*[\)\]]\s*\d*(?:\.\d+)?"
_RUN = re.compile(r"(?:" + _TOK + r"|" + _GRP + r")(?:\s*(?:" + _TOK + r"|" + _GRP + r"))*")


def _scan_formula_runs(s):
    """Yield contiguous formula-like spans, permitting inter-token spaces.

    A run is kept only if it contains a digit (explicit stoichiometry) or a
    parenthesised group -- this filters out prose stretches while tolerating
    the space-separated formulas ("La 2 CuO 4") that abound in SuperMat.
    """
    out = []
    for m in _RUN.finditer(s):
        tok = m.group(0).strip()
        if not tok:
            continue
        if not re.search(r"\d", tok) and "(" not in tok and "[" not in tok:
            continue
        # must contain at least one element-like symbol
        if not re.search(r"[A-Z]", tok):
            continue
        out.append(tok)
    return out


def _fuzzy(c):
    # round tiny float errors
    return {el: round(v, 4) for el, v in c.items()}


def compare_compositions(ce, cp):
    ce = _fuzzy(ce)
    cp = _fuzzy(cp)
    for el, v in ce.items():
        if el not in cp or _fuzzy({el: cp[el]})[el] != v:
            return False
    return True


def _strings_equivalent(e, p):
    return e.strip().lower().replace(" ", "") == p.strip().lower().replace(" ", "")


def match_by_formula(expected_str, predicted_str, matcher=None):
    """Replicate commons.evaluation.match_by_formula semantics."""
    if matcher is None:
        matcher = parse_material
    e = expected_str
    p = predicted_str
    if not e:
        return True
    if _strings_equivalent(e, p):
        return True
    if not p:
        return False
    ce_list = matcher(e)
    cp_list = matcher(p)
    for ce in ce_list:
        for cpp in cp_list:
            if type(ce) is dict and type(cpp) is dict:
                if compare_compositions(ce, cpp):
                    return True
            elif type(ce) is str and type(cpp) is str:
                if ce == cpp:
                    return True
    return False


def compute_formula_tp_fp(expected_in_pid, predicted_in_pid, matcher=None):
    """Greedy one-to-one formula match within a paragraph bucket.

    Returns (tp_count, fp_count, fn_count, errors) where errors lists
    (expected, predicted) pairs flagged by a human-look filter."""
    if matcher is None:
        matcher = parse_material
    tp, fp, fn = [], [], []
    skip_predicted, skip_expected = set(), set()
    for idxp, predicted_entity in enumerate(predicted_in_pid):
        if idxp in skip_predicted:
            continue
        matched = False
        for idxe, expected_entity in enumerate(expected_in_pid):
            if idxe in skip_expected:
                continue
            if match_by_formula(expected_entity, predicted_entity, matcher):
                tp.append((expected_entity, predicted_entity))
                skip_predicted.add(idxp)
                skip_expected.add(idxe)
                matched = True
                break
        if not matched:
            fp.append(predicted_entity)
    for idxe, expected_entity in enumerate(expected_in_pid):
        if idxe not in skip_expected:
            fn.append(expected_entity)
    return tp, fp, fn