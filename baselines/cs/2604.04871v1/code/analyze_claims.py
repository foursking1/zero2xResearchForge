#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StatsClaw claim analysis for arXiv:2604.04871v1 (TASK claims C01-C04).

Analyzes the frozen reproduction workspace at F:/dataset/24_2604.04871v1
(original statsclaw framework source + example-probit package + Monte Carlo data)
and compares the four architecture claims against:
  (a) the paper text (extracted from the frozen PDF), and
  (b) the actual StatsClaw framework source in statsclaw_repo/.

Outputs:
  results/evidence_table.csv   - flat evidence table
  results/metrics.json         - machine-readable key metrics
  results/paper_text.txt       - extracted paper text (traceability)
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (frozen data in place; nothing copied)
# ---------------------------------------------------------------------------
DATA_ROOT = Path(r"F:/dataset/24_2604.04871v1")
REPO = DATA_ROOT / "statsclaw_repo"
AGENTS_DIR = REPO / "agents"
PROTOCOL = REPO / "skills" / "statsclaw-protocol" / "SKILL.md"
ISOLATION = REPO / "skills" / "isolation" / "SKILL.md"
REPO_README = REPO / "README.md"
LEADER = AGENTS_DIR / "leader.md"
BUILDER = AGENTS_DIR / "builder.md"
TESTER = AGENTS_DIR / "tester.md"
SIMULATOR = AGENTS_DIR / "simulator.md"
PLANNER = AGENTS_DIR / "planner.md"
DISTILLER = AGENTS_DIR / "distiller.md"
PDF = DATA_ROOT / "arxiv_2604.04871v1_original.pdf"
MC_CSV = DATA_ROOT / "data" / "monte_carlo_results.csv"
OUT_DIR = Path(__file__).resolve().parent.parent / "results"

EVIDENCE = []  # rows: dict(claim_id, metric, value, unit, source, note)


def add_evidence(claim_id: str, metric: str, value, unit: str, source: str, note: str = ""):
    EVIDENCE.append({
        "claim_id": claim_id,
        "metric": metric,
        "value": value if isinstance(value, (str, type(None))) else f"{value:.6g}",
        "unit": unit,
        "source": source,
        "note": note,
    })


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def norm_ws(text: str) -> str:
    """Collapse all whitespace so phrases split across pdftotext lines still match."""
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# 0. Extract paper text (frozen PDF) -> results/paper_text.txt
# ---------------------------------------------------------------------------
def extract_paper_text() -> str:
    out_txt = OUT_DIR / "paper_text.txt"
    if not out_txt.exists():
        try:
            r = subprocess.run(
                ["pdftotext", "-layout", str(PDF), "-"],
                capture_output=True, check=True, timeout=180,
            )
            text = r.stdout.decode("utf-8", errors="replace")
        except Exception as e:  # pragma: no cover
            print("pdftotext failed:", e)
            text = ""
    else:
        text = out_txt.read_text(encoding="utf-8", errors="replace")
    out_txt.write_text(text, encoding="utf-8")
    return text


# ---------------------------------------------------------------------------
# C01: multi-agent architecture + information barriers
# ---------------------------------------------------------------------------
def analyze_c01(paper_text: str, metrics: dict):
    paper_norm = norm_ws(paper_text)

    agent_files = sorted(AGENTS_DIR.glob("*.md"))
    agent_names = [p.stem for p in agent_files]
    n_agents = len(agent_files)

    roles = {}
    for p in agent_files:
        m = re.search(r"description:\s*\"([^\"]+)\"", read_text(p))
        roles[p.stem] = m.group(1) if m else ""

    builder_txt = read_text(BUILDER)
    tester_txt = read_text(TESTER)
    sim_txt = read_text(SIMULATOR)
    agent_texts = {"builder": builder_txt, "tester": tester_txt, "simulator": sim_txt}

    # barrier matrix: (agent, forbidden artifact, mode) must be explicitly excluded
    barrier_spec = [
        # (agent, artifact, mode, regex)
        ("builder", "test-spec.md", "NEVER READS", r"NEVER READS[^\n]*test-spec\.md"),
        ("builder", "test-spec.md", "MUST NOT read", r"MUST NOT read test-spec\.md"),
        ("tester", "spec.md", "NEVER READS", r"NEVER READS[^\n]*spec\.md"),
        ("tester", "implementation.md", "NEVER READS", r"NEVER READS[^\n]*implementation\.md"),
        ("tester", "spec.md", "MUST NOT read", r"MUST NOT read spec\.md"),
        ("tester", "implementation.md", "MUST NOT read", r"MUST NOT read implementation\.md"),
        ("simulator", "spec.md", "Never receives", r"Never receives[^\n]*spec\.md"),
        ("simulator", "test-spec.md", "Never receives", r"Never receives[^\n]*test-spec\.md"),
        ("simulator", "spec.md", "MUST NOT read", r"MUST NOT read `?spec\.md`?"),
        ("simulator", "test-spec.md", "MUST NOT read", r"MUST NOT read `?test-spec\.md`?"),
    ]
    barrier_results = []
    for agent, artifact, mode, pattern in barrier_spec:
        hit = bool(re.search(pattern, agent_texts[agent], flags=re.MULTILINE))
        barrier_results.append((agent, artifact, mode, hit))

    # positive control: each execution agent DOES receive its own primary spec
    primary_receives = [
        ("builder", "spec.md", r"READS[^\n]*spec\.md"),
        ("tester", "test-spec.md", r"READS[^\n]*test-spec\.md"),
        ("simulator", "sim-spec.md", r"Receives[^\n]*sim-spec\.md"),
    ]
    primary_hits = []
    for agent, artifact, pattern in primary_receives:
        primary_hits.append((agent, artifact, bool(re.search(pattern, agent_texts[agent], flags=re.MULTILINE))))

    # isolation skill pipeline table
    iso_txt = read_text(ISOLATION)
    iso_pipeline_rules = {
        "builder receives spec.md only": bool(re.search(r"builder.*?Receives.*spec\.md", iso_txt, re.S)),
        "builder never receives test-spec": bool(re.search(r"builder.*Never receives.*test-spec\.md", iso_txt, re.S)),
        "tester receives test-spec.md only": bool(re.search(r"tester.*?Receives.*test-spec\.md", iso_txt, re.S)),
        "tester never receives spec.md": bool(re.search(r"tester.*Never receives.*spec\.md", iso_txt, re.S)),
        "simulator receives sim-spec.md only": bool(re.search(r"simulator.*?Receives.*sim-spec\.md", iso_txt, re.S)),
        "simulator never receives spec/test-spec": bool(re.search(r"simulator.*Never receives.*spec\.md", iso_txt, re.S)),
        "reviewer sees all artifacts": bool(re.search(r"reviewer.*?Receives.*ALL", iso_txt, re.S)),
    }

    leader_txt = read_text(LEADER)
    dispatch_rule = bool(re.search(r"MUST NOT pass spec\.md to tester", leader_txt))

    paper_multiagent = ("multi-agent" in paper_norm) or ("specialized agents" in paper_norm)
    paper_barrier = bool(re.search(r"information barriers between code generation and code validation", paper_norm))

    metrics["c01"] = {
        "n_agent_files": n_agents,
        "agent_names": agent_names,
        "agent_roles": roles,
        "barrier_checks_passed": sum(1 for _, _, _, h in barrier_results if h),
        "barrier_checks_total": len(barrier_results),
        "barrier_results": [{"agent": a, "artifact": ar, "mode": m, "ok": h}
                            for a, ar, m, h in barrier_results],
        "primary_spec_received": [{"agent": a, "artifact": ar, "ok": h} for a, ar, h in primary_hits],
        "isolation_skill_rules_true": sum(1 for v in iso_pipeline_rules.values() if v),
        "isolation_skill_rules_total": len(iso_pipeline_rules),
        "leader_dispatch_rule_present": dispatch_rule,
        "paper_mentions_multiagent_or_specialized": paper_multiagent,
        "paper_mentions_information_barrier": paper_barrier,
    }
    add_evidence("C01", "n_agent_files_in_repo", n_agents, "count",
                 "statsclaw_repo/agents/*.md", "multi-agent evidence")
    add_evidence("C01", "information_barrier_checks_passed",
                 f"{metrics['c01']['barrier_checks_passed']}/{len(barrier_results)}",
                 "checks", "grep of agents/builder.md,tester.md,simulator.md",
                 "explicit exclusion of cross-pipeline artifacts")
    add_evidence("C01", "primary_spec_received_checks",
                 f"{sum(1 for _, _, h in primary_hits if h)}/{len(primary_hits)}",
                 "checks", "agents/builder.md,tester.md,simulator.md",
                 "each execution agent receives its own primary spec")
    add_evidence("C01", "isolation_skill_pipeline_rules_true",
                 f"{metrics['c01']['isolation_skill_rules_true']}/{len(iso_pipeline_rules)}",
                 "rules", "skills/isolation/SKILL.md")
    add_evidence("C01", "leader_dispatch_isolation_rule", dispatch_rule, "bool",
                 "agents/leader.md", "MUST NOT pass spec.md to tester")
    add_evidence("C01", "paper_information_barrier_statement", paper_barrier, "bool",
                 "arxiv PDF abstract",
                 "quote: 'information barriers between code generation and code validation'")
    return metrics


# ---------------------------------------------------------------------------
# C02: eight specialized agents within a single Claude Code session
# ---------------------------------------------------------------------------
def analyze_c02(paper_text: str, metrics: dict):
    paper_norm = norm_ws(paper_text)
    agent_files = sorted(AGENTS_DIR.glob("*.md"))
    agent_names = [p.stem for p in agent_files]
    n_files = len(agent_files)

    m8 = re.search(r"StatsClaw orchestrates (eight|nine) specialized agents([0-9])", paper_norm)
    paper_count_claim = m8.group(1) if m8 else None
    paper_ninth_footnote = bool(re.search(r"The current implementation includes a ninth agent", paper_norm))

    appendix_agents = ["Leader", "Planner", "Builder", "Tester", "Simulator", "Scriber", "Reviewer", "Shipper"]
    found_in_appendix = [a for a in appendix_agents if re.search(rf"\b{a}\b", paper_text)]

    dist_txt = read_text(DISTILLER)
    distiller_brain_gated = "brain" in dist_txt.lower()

    readme_txt = read_text(REPO_README)
    # matches: "a team of **9 specialized AI agents**" (bold may wrap the whole phrase)
    m9 = re.search(r"a team of[^\d]*(\d+)[^\d]*specialized AI agents", readme_txt)
    readme_count = int(m9.group(1)) if m9 else None

    protocol_txt = read_text(PROTOCOL)
    repo_uses_agent_tool = "Agent tool" in protocol_txt
    paper_single_session = "single Claude Code session" in paper_norm

    metrics["c02"] = {
        "n_agent_files_in_repo": n_files,
        "repo_agent_names": agent_names,
        "paper_stated_agent_count": paper_count_claim,
        "paper_footnote_ninth_agent": paper_ninth_footnote,
        "appendix_A1_agents_found": len(found_in_appendix),
        "appendix_A1_agents_total": len(appendix_agents),
        "distiller_brain_mode_only": distiller_brain_gated,
        "repo_readme_agent_count": readme_count,
        "paper_single_session_claim": paper_single_session,
        "repo_dispatches_via_agent_tool": repo_uses_agent_tool,
    }
    add_evidence("C02", "agent_definition_files", n_files, "count",
                 "statsclaw_repo/agents/*.md",
                 "paper main text says eight; repo defines nine (8 core + optional distiller)")
    add_evidence("C02", "paper_stated_agent_count", paper_count_claim, "count",
                 "arxiv PDF (main text)",
                 "footnote: ninth agent (distiller) optional brain-mode only, default disabled")
    add_evidence("C02", "appendix_A1_agents_matched", f"{len(found_in_appendix)}/{len(appendix_agents)}",
                 "agents", "arxiv PDF Appendix A Table A1",
                 "Leader, Planner, Builder, Tester, Simulator, Scriber, Reviewer, Shipper")
    add_evidence("C02", "repo_readme_agent_count", readme_count, "count",
                 "statsclaw_repo/README.md", "repo README states its own agent-team size")
    add_evidence("C02", "single_claude_code_session_claim", paper_single_session, "bool",
                 "arxiv PDF (main text)")
    add_evidence("C02", "repo_dispatches_via_claude_code_agent_tool", repo_uses_agent_tool, "bool",
                 "skills/statsclaw-protocol/SKILL.md",
                 "'You MUST use the Agent tool to dispatch every teammate'")
    return metrics


# ---------------------------------------------------------------------------
# C03: planner produces independent specification documents for separate agents
# ---------------------------------------------------------------------------
def analyze_c03(paper_text: str, metrics: dict):
    paper_norm = norm_ws(paper_text)
    plan_txt = read_text(PLANNER)
    iso_txt = read_text(ISOLATION)

    produces_spec = "spec.md" in plan_txt
    produces_testspec = "test-spec.md" in plan_txt
    produces_simspec = "sim-spec.md" in plan_txt
    independent_sufficient = plan_txt.count("independently sufficient")
    must_not_leak = bool(re.search(r"MUST NOT leak implementation details into test-spec\.md", plan_txt))

    dispatch_builder = bool(re.search(r"include `spec\.md` in the prompt, NEVER mention `test-spec\.md`", iso_txt))
    dispatch_tester = bool(re.search(r"include `test-spec\.md` in the prompt, NEVER mention `spec\.md`", iso_txt))
    dispatch_sim = bool(re.search(r"include `sim-spec\.md` in the prompt, NEVER mention `spec\.md`", iso_txt))

    paper_three_docs = bool(re.search(r"produces three self-contained specification documents", paper_norm))
    paper_two_independent = bool(re.search(r"produces two independent documents", paper_norm))
    paper_neither_sees = bool(re.search(r"Neither agent sees the other's document", paper_norm))

    spec_artifacts = list(DATA_ROOT.rglob("spec.md")) + list(DATA_ROOT.rglob("test-spec.md")) + \
                     list(DATA_ROOT.rglob("sim-spec.md"))
    spec_artifact_paths = [str(p.relative_to(DATA_ROOT)) for p in spec_artifacts]
    input_pdf = list(DATA_ROOT.rglob("probit_spec.pdf"))

    metrics["c03"] = {
        "planner_produces_spec_md": produces_spec,
        "planner_produces_test_spec_md": produces_testspec,
        "planner_produces_sim_spec_md": produces_simspec,
        "independent_sufficient_mentions": independent_sufficient,
        "planner_no_leak_rule": must_not_leak,
        "dispatch_builder_isolated": dispatch_builder,
        "dispatch_tester_isolated": dispatch_tester,
        "dispatch_simulator_isolated": dispatch_sim,
        "paper_three_specs_claim": paper_three_docs,
        "paper_two_independent_docs_claim": paper_two_independent,
        "paper_neither_agent_sees_other": paper_neither_sees,
        "spec_artifacts_in_frozen_data": len(spec_artifact_paths),
        "input_pdf_spec_present": len(input_pdf),
    }
    add_evidence("C03", "planner_produces_spec.md", produces_spec, "bool", "agents/planner.md")
    add_evidence("C03", "planner_produces_test-spec.md", produces_testspec, "bool", "agents/planner.md")
    add_evidence("C03", "planner_produces_sim-spec.md", produces_simspec, "bool", "agents/planner.md",
                 "simulation workflows 11/12 only")
    add_evidence("C03", "independently_sufficient_mentions", independent_sufficient, "count", "agents/planner.md")
    add_evidence("C03", "dispatch_builder_test_spec_isolated", dispatch_builder, "bool",
                 "skills/isolation/SKILL.md", "leader dispatch: builder NEVER mention test-spec.md")
    add_evidence("C03", "dispatch_tester_spec_isolated", dispatch_tester, "bool",
                 "skills/isolation/SKILL.md", "leader dispatch: tester NEVER mention spec.md")
    add_evidence("C03", "dispatch_simulator_spec_isolated", dispatch_sim, "bool",
                 "skills/isolation/SKILL.md", "leader dispatch: simulator NEVER mention spec.md")
    add_evidence("C03", "paper_planner_three_documents", paper_three_docs, "bool",
                 "arxiv PDF Section 2.2",
                 "quote: 'the planner produces three self-contained specification documents'")
    add_evidence("C03", "spec_artifacts_in_frozen_data", len(spec_artifact_paths), "count",
                 "rglob over data root",
                 "run-directory spec.md/test-spec.md/sim-spec.md live in workspace repo (not frozen)")
    return metrics


# ---------------------------------------------------------------------------
# C04: state machine with sequential gates / mandatory preconditions
# ---------------------------------------------------------------------------
def analyze_c04(paper_text: str, metrics: dict):
    paper_norm = norm_ws(paper_text)
    proto_txt = read_text(PROTOCOL)

    m = re.search(r"`(CREDENTIALS_VERIFIED)`\s*→\s*`(NEW)`.*?`(DONE)`", proto_txt, re.S)
    state_chain_raw = m.group(0).replace("\n", " ") if m else ""
    states = re.findall(r"`([A-Z_]+)`", state_chain_raw)
    states = list(dict.fromkeys(states))

    interrupt_states = ["HOLD", "BLOCKED", "STOPPED"]
    present_interrupts = [s for s in interrupt_states if f"`{s}`" in proto_txt or s in proto_txt]

    precond_sec = re.search(r"## Hard Enforcement: State Transition Preconditions(.*?)(?:## |\Z)", proto_txt, re.S)
    precond_text = precond_sec.group(1) if precond_sec else ""
    # each row: | Target State | Precondition | Verification |
    precond_rows = re.findall(r"^\|\s*`?([A-Z_]+)`?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", precond_text, re.M)
    precond_targets = sorted(set(r[0] for r in precond_rows))

    n_core_states = len(states) - (1 if "KNOWLEDGE_EXTRACTED" in states else 0)

    leader_txt = read_text(LEADER)
    leader_gate = bool(re.search(r"Gate state transitions on artifact existence and preconditions", leader_txt))

    paper_mandatory_preconditions = bool(re.search(r"mandatory preconditions at each transition", paper_norm))
    paper_nine_states = "nine states" in paper_norm
    paper_hard_gates = bool(re.search(r"hard gates at each transition", paper_norm))

    metrics["c04"] = {
        "state_chain": states,
        "n_states_total_named": len(states),
        "n_states_core_non_optional": n_core_states,
        "interrupt_states_present": present_interrupts,
        "precondition_table_targets": precond_targets,
        "n_precondition_rows": len(precond_rows),
        "leader_gate_on_preconditions": leader_gate,
        "paper_mandatory_preconditions": paper_mandatory_preconditions,
        "paper_nine_states_claim": paper_nine_states,
        "paper_hard_gates": paper_hard_gates,
    }
    add_evidence("C04", "n_states_in_state_model", len(states), "count",
                 "skills/statsclaw-protocol/SKILL.md", "chain: " + " → ".join(states))
    add_evidence("C04", "n_core_non_optional_states", n_core_states, "count",
                 "skills/statsclaw-protocol/SKILL.md",
                 "excludes optional KNOWLEDGE_EXTRACTED; paper says 'nine states'")
    add_evidence("C04", "n_interrupt_states", len(present_interrupts), "count",
                 "skills/statsclaw-protocol/SKILL.md", ", ".join(present_interrupts))
    add_evidence("C04", "n_precondition_rows", len(precond_rows), "rows",
                 "skills/statsclaw-protocol/SKILL.md",
                 "Hard Enforcement: State Transition Preconditions table")
    add_evidence("C04", "precondition_target_states", "|".join(precond_targets), "states",
                 "skills/statsclaw-protocol/SKILL.md")
    add_evidence("C04", "leader_gates_on_preconditions", leader_gate, "bool", "agents/leader.md")
    add_evidence("C04", "paper_mandatory_preconditions", paper_mandatory_preconditions, "bool", "arxiv PDF")
    add_evidence("C04", "paper_nine_states_claim", paper_nine_states, "bool", "arxiv PDF")
    return metrics


# ---------------------------------------------------------------------------
# Supplementary: numerical sanity check of StatsClaw-produced package results
# ---------------------------------------------------------------------------
def analyze_supplementary(metrics: dict):
    try:
        import pandas as pd
        df = pd.read_csv(MC_CSV)
        n_rows = len(df)
        coverage_range = (float(df["coverage"].min()), float(df["coverage"].max()))
        n_fail_total = int(df["n_fail"].sum())
        n_valid_total = int(df["n_valid"].sum())
        mle5 = df[(df["N"] == 5000) & (df["method"] == "MLE")]
        max_bias_5000 = float(mle5["bias"].abs().max())
        ratios = {}
        for N in sorted(df["N"].unique()):
            sub = df[(df["N"] == N) & (df["param"] == "beta_0")]
            mle_b0 = sub[sub["method"] == "MLE"]["rmse"].iloc[0]
            gibbs_b0 = sub[sub["method"] == "Gibbs"]["rmse"].iloc[0]
            ratios[str(N)] = round(float(gibbs_b0 / mle_b0), 3)
        mh_acc = df[df["method"] == "MH"]["accept_rate"].dropna()
        acc_range = (round(float(mh_acc.min()), 4), round(float(mh_acc.max()), 4)) if len(mh_acc) else None
        time_ratios = {}
        for N in sorted(df["N"].unique()):
            t_mle = df[(df["N"] == N) & (df["method"] == "MLE")]["time"].iloc[0]
            t_gibbs = df[(df["N"] == N) & (df["method"] == "Gibbs")]["time"].iloc[0]
            time_ratios[str(N)] = round(float(t_gibbs / t_mle), 1)
        # RMSE decay from N=200 to N=5000 (paper: ~1/sqrt(N), expected ~sqrt(25)=5.0)
        rmse_decay = {}
        for param in ["beta_0", "beta_1"]:
            r200 = df[(df["N"] == 200) & (df["method"] == "MLE") & (df["param"] == param)]["rmse"].iloc[0]
            r5000 = df[(df["N"] == 5000) & (df["method"] == "MLE") & (df["param"] == param)]["rmse"].iloc[0]
            rmse_decay[param] = round(float(r200 / r5000), 2)
        metrics["supplementary"] = {
            "monte_carlo_rows": n_rows,
            "coverage_range": coverage_range,
            "total_failures": n_fail_total,
            "total_valid_reps": n_valid_total,
            "max_abs_mle_bias_N5000": max_bias_5000,
            "rmse_ratio_gibbs_over_mle_beta0": ratios,
            "mh_acceptance_rate_range": acc_range,
            "time_ratio_gibbs_over_mle": time_ratios,
            "rmse_decay_ratio_N200_to_N5000_mle": rmse_decay,
        }
        add_evidence("SUPP", "monte_carlo_total_replications", n_valid_total, "reps", str(MC_CSV))
        add_evidence("SUPP", "monte_carlo_failures", n_fail_total, "count", str(MC_CSV))
        add_evidence("SUPP", "coverage_range", f"[{coverage_range[0]}, {coverage_range[1]}]", "range", str(MC_CSV))
        add_evidence("SUPP", "max_abs_mle_bias_N5000", max_bias_5000, "abs", str(MC_CSV))
        add_evidence("SUPP", "mh_acceptance_rate_range", f"{acc_range}", "range", str(MC_CSV))
        add_evidence("SUPP", "rmse_decay_ratio_N200_to_N5000_mle", f"{rmse_decay}", "ratio", str(MC_CSV),
                     "paper: RMSE decreases at ~1/sqrt(N); expected ratio sqrt(5000/200)~5.0")
    except Exception as e:  # pragma: no cover
        metrics["supplementary"] = {"error": str(e)}
        add_evidence("SUPP", "monte_carlo_analysis", "ERROR", "-", str(MC_CSV), str(e))
    return metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paper_text = extract_paper_text()

    metrics = {"task": "2604.04871v1", "data_root": str(DATA_ROOT)}
    metrics = analyze_c01(paper_text, metrics)
    metrics = analyze_c02(paper_text, metrics)
    metrics = analyze_c03(paper_text, metrics)
    metrics = analyze_c04(paper_text, metrics)
    metrics = analyze_supplementary(metrics)

    with open(OUT_DIR / "evidence_table.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["claim_id", "metric", "value", "unit", "source", "note"])
        w.writeheader()
        w.writerows(EVIDENCE)

    with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(json.dumps({k: metrics[k] for k in ["c01", "c02", "c03", "c04", "supplementary"]},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
