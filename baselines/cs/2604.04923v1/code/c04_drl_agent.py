"""C04: Verify the trained DRL agent (Transformer-XL + PPO, STL robustness reward).

The frozen workspace ships:
  * results/config.json          - d_model=64, nhead=4, num_blocks=1,
                                   history_length=5, total_steps=10000, PPO
                                   hyper-parameters, model_params=151818.
  * results/training_stats.json  - total_episodes=51, avg_reward =
                                   avg_stl_robustness = 0.7627.
  * results/checkpoints/checkpoint_final.pt - model_state_dict, optimizer
                                   state, episode_rewards, episode_stl_robustness.
  * code/transformer_model.py    - PPOActorCritic with a Transformer-XL
                                   backbone (reference implementation).
  * code/simple_grid_env.py      - SimpleGridEnv (gymnasium) used for training.

This script (a) rebuilds the architecture from the frozen reference and loads
the checkpoint, (b) runs a forward pass to confirm the checkpoint is usable,
and (c) evaluates the trained policy (greedy and sampling) against a
random-action baseline on a numpy re-implementation of SimpleGridEnv (gymnasium
is not required), using the same shaped reward and terminal STL robustness of
the reference env.  It also analyses the learned action distribution to
characterise the trained policy.

Question: does a trained DRL agent with Transformer-XL + PPO using an STL
robustness reward exist and perform satisfactorily (C04)?
"""
import os
import json
import sys

import numpy as np
import torch

# Tiny transformer on this multi-core box is much faster single-threaded
# (12-thread contention makes each forward pass ~20x slower).
torch.set_num_threads(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA_ROOT, RESULTS_ROOT, load_config, load_training_stats,  # noqa: E402
                    load_checkpoint)
# the frozen reference model implementation
sys.path.insert(0, os.path.join(DATA_ROOT, "code"))
from transformer_model import PPOActorCritic  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


# ---------------------------------------------------------------------------
# Numpy re-implementation of the SimpleGrid environment (reference: the frozen
# simple_grid_env.py).  Same dynamics, shaped reward and STL robustness.
# ---------------------------------------------------------------------------
ACTION_MAP = {
    0: (-1, 0),   # Up
    1: (1, 0),    # Down
    2: (0, -1),   # Left
    3: (0, 1),    # Right
    4: (-1, -1),  # Up-Left
    5: (-1, 1),   # Up-Right
    6: (1, -1),   # Down-Left
    7: (1, 1),    # Down-Right
    8: (0, 0),    # No-op
}


class SimpleGridEnvNumpy:
    """Grid-world navigation task with a temporal 'eventually' STL formula.

    Reference: code/simple_grid_env.py (SimpleGridEnv, formula_type='eventually').
    """

    def __init__(self, grid_size=10, max_steps=195,
                 temporal_window=(92, 165), seed=None):
        self.grid_size = grid_size
        self.max_steps = max_steps
        self.temporal_window = temporal_window
        self.rng = np.random.default_rng(seed)
        self.reset()

    def reset(self):
        self.agent_pos = self.rng.integers(0, self.grid_size, size=2)
        while True:
            self.green_target = self.rng.integers(0, self.grid_size, size=2)
            if not np.array_equal(self.agent_pos, self.green_target):
                break
        self.step_count = 0
        self.trajectory = []
        return self._obs()

    def _obs(self):
        return np.array([self.agent_pos[0], self.agent_pos[1],
                         self.green_target[0], self.green_target[1],
                         self.step_count / self.max_steps], dtype=np.float32)

    def step(self, action):
        dx, dy = ACTION_MAP[int(action)]
        new_pos = self.agent_pos + np.array([dx, dy])
        self.agent_pos = np.clip(new_pos, 0, self.grid_size - 1)
        self.step_count += 1
        self.trajectory.append({
            'position': self.agent_pos.copy(),
            'timestep': self.step_count,
        })
        dist = int(np.sum(np.abs(self.agent_pos - self.green_target)))
        reward = 1.0 - dist / (2 * self.grid_size)
        terminated = self.step_count >= self.max_steps
        stl = self._stl_robustness() if terminated else None
        return self._obs(), reward, terminated, stl

    def _stl_robustness(self):
        """Eventually formula: max green robustness inside temporal window."""
        window = [t for t in self.trajectory
                  if self.temporal_window[0] <= t['timestep'] <= self.temporal_window[1]]
        if len(window) == 0:
            return -1.0
        vals = [1.0 - int(np.sum(np.abs(t['position'] - self.green_target))) / (2 * self.grid_size)
                for t in window]
        return float(max(vals))


def build_model(cfg):
    model = PPOActorCritic(
        obs_shape=(5,), action_dim=9,
        d_model=cfg["d_model"], nhead=cfg["nhead"],
        num_blocks=cfg["num_blocks"], history_length=cfg["history_length"],
    )
    return model


def run_episode(model, env, greedy=True, device="cpu", history_length=5):
    """Run one episode with the model policy (or random if model is None)."""
    obs = env.reset()
    history = [obs] * (history_length if model is not None else 0)
    total_reward = 0.0
    stl = 0.0
    for _ in range(env.max_steps):
        if model is None:
            action = int(env.rng.integers(0, 9))
        else:
            obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(device)
            hist_t = torch.tensor(np.array(history), dtype=torch.float32).unsqueeze(0).to(device)
            with torch.no_grad():
                probs, _, _ = model(obs_t, hist_t)
                logits = torch.log(probs[0] + 1e-8)
            action = int(logits.argmax().item()) if greedy else int(torch.multinomial(probs[0], 1).item())
        obs, reward, terminated, stl = env.step(action)
        total_reward += reward
        if model is not None:
            history = (history + [obs])[-history_length:]
        if terminated:
            break
    return total_reward, stl


def evaluate_policy(model, n_episodes, greedy, seed, device="cpu", history_length=5):
    """Evaluate a policy over a fixed set of episode starts."""
    rewards = []
    stls = []
    successes = []
    env = SimpleGridEnvNumpy(seed=seed)
    for _ in range(n_episodes):
        r, s = run_episode(model, env, greedy=greedy, device=device,
                           history_length=history_length)
        rewards.append(r)
        stls.append(s)
        successes.append(1.0 if s >= 0.95 else 0.0)
    return rewards, stls, successes


def action_distribution(model, n_samples=300, device="cpu", history_length=5):
    """Mean action distribution of the trained policy over random observations."""
    rng = np.random.default_rng(0)
    probs_acc = []
    argmax_counts = np.zeros(9, dtype=int)
    entropies = []
    for _ in range(n_samples):
        obs = rng.uniform(0, 10, size=(5,)).astype(np.float32)
        obs[4] = rng.uniform(0, 1)
        hist = rng.uniform(0, 10, size=(history_length, 5)).astype(np.float32)
        obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(device)
        hist_t = torch.tensor(hist, dtype=torch.float32).unsqueeze(0).to(device)
        with torch.no_grad():
            probs, _, _ = model(obs_t, hist_t)
        p = probs[0].cpu().numpy()
        probs_acc.append(p)
        argmax_counts[int(p.argmax())] += 1
        p_safe = np.clip(p, 1e-12, 1.0)
        entropies.append(float(-(p_safe * np.log(p_safe)).sum()))
    probs_acc = np.array(probs_acc)
    return {
        "n_samples": n_samples,
        "mean_action_probs": [float(x) for x in probs_acc.mean(axis=0)],
        "argmax_action_counts": [int(x) for x in argmax_counts],
        "argmax_dominant_action": int(argmax_counts.argmax()),
        "mean_entropy": float(np.mean(entropies)),
        "max_entropy_9_actions": float(np.log(9)),
    }


def main():
    cfg = load_config()
    stats = load_training_stats()
    ckpt = load_checkpoint("checkpoint_final.pt", map_location="cpu")

    # ---- 1. architecture + checkpoint consistency ----
    model = build_model(cfg)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    state_dict = ckpt["model_state_dict"]
    n_params = sum(p.numel() for p in model.parameters())
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    pe_buffer = state_dict.get("transformer.pos_encoder.pe")

    # forward pass on a dummy observation
    obs_dummy = torch.zeros(1, 5)
    hist_dummy = torch.zeros(1, cfg["history_length"], 5)
    with torch.no_grad():
        probs, value, latent = model(obs_dummy, hist_dummy)
    fwd = {
        "action_probs_shape": list(probs.shape),
        "value_shape": list(value.shape),
        "latent_shape": list(latent.shape),
        "probs_sum": float(probs.sum().item()),
        "n_actions": int(cfg["history_length"] and 9),
    }

    # training recorded episode STL robustness
    ep_rewards = list(ckpt.get("episode_rewards", []))
    ep_stl = list(ckpt.get("episode_stl_robustness", []))
    # NOTE: the reproduction wrote the STL robustness value into BOTH fields;
    # check whether the two lists are literally identical.
    fields_identical = bool(np.allclose(ep_rewards, ep_stl)) and len(ep_rewards) == len(ep_stl)

    # ---- 2. policy evaluation on the numpy SimpleGrid env ----
    n_episodes = 100
    device = "cpu"
    # identical episode starts for all three policies -> apples-to-apples
    eval_seed = 1234

    tr_g_rewards, tr_g_stl, tr_g_succ = evaluate_policy(
        model, n_episodes, greedy=True, seed=eval_seed, device=device)
    tr_s_rewards, tr_s_stl, tr_s_succ = evaluate_policy(
        model, n_episodes, greedy=False, seed=eval_seed, device=device)
    rnd_rewards, rnd_stl, rnd_succ = evaluate_policy(
        None, n_episodes, greedy=True, seed=eval_seed)

    def _block(rewards, stls, successes):
        return {
            "mean_shaped_reward": float(np.mean(rewards)),
            "std_shaped_reward": float(np.std(rewards)),
            "mean_stl_robustness": float(np.mean(stls)),
            "std_stl_robustness": float(np.std(stls)),
            "success_rate_ge095": float(np.mean(successes)),
        }

    eval_res = {
        "n_episodes": n_episodes,
        "shared_episode_seed": eval_seed,
        "trained_greedy": _block(tr_g_rewards, tr_g_stl, tr_g_succ),
        "trained_sampling": _block(tr_s_rewards, tr_s_stl, tr_s_succ),
        "random_policy": _block(rnd_rewards, rnd_stl, rnd_succ),
        "trained_greedy_vs_random_stl_gap": float(np.mean(tr_g_stl) - np.mean(rnd_stl)),
        "trained_greedy_vs_random_shaped_gap": float(np.mean(tr_g_rewards) - np.mean(rnd_rewards)),
    }

    # ---- 3. trained policy action distribution ----
    adist = action_distribution(model, n_samples=300, device=device,
                                history_length=cfg["history_length"])

    summary = {
        "config": cfg,
        "training_stats_reported": stats,
        "checkpoint": {
            "exists": True,
            "keys": sorted(state_dict.keys()),
            "n_model_params": int(n_params),
            "n_trainable_params": int(n_trainable),
            "config_model_params": cfg["model_params"],
            "params_match_config": bool(n_params == cfg["model_params"]),
            "pos_encoder_pe_buffer_shape": (list(pe_buffer.shape) if pe_buffer is not None else None),
            "n_episode_rewards_saved": len(ep_rewards),
            "n_episode_stl_saved": len(ep_stl),
            "saved_episode_rewards_mean": float(np.mean(ep_rewards)) if ep_rewards else None,
            "saved_episode_stl_mean": float(np.mean(ep_stl)) if ep_stl else None,
            "saved_episode_stl_range": [float(min(ep_stl)), float(max(ep_stl))] if ep_stl else None,
            "episode_rewards_identical_to_episode_stl": bool(fields_identical),
        },
        "forward_pass": fwd,
        "architecture": {
            "type": "PPOActorCritic(Transformer-XL backbone)",
            "d_model": cfg["d_model"],
            "nhead": cfg["nhead"],
            "num_blocks": cfg["num_blocks"],
            "history_length": cfg["history_length"],
            "obs_dim": 5,
            "action_dim": 9,
            "token_input_size": 5 * (cfg["history_length"] + 1),
        },
        "evaluation": eval_res,
        "action_distribution": adist,
    }

    with open(os.path.join(OUT_DIR, "c04_drl_agent.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---- console ----
    print("=== C04: trained DRL agent verification ===")
    print(f"config: d_model={cfg['d_model']} nhead={cfg['nhead']} num_blocks={cfg['num_blocks']} "
          f"history={cfg['history_length']} total_steps={cfg['total_steps']}")
    print(f"params: model={n_params} config={cfg['model_params']} match={n_params == cfg['model_params']}")
    print(f"training reported: episodes={stats['total_episodes']} avg_reward={stats['avg_reward']:.4f} "
          f"avg_stl={stats['avg_stl_robustness']:.4f}")
    print(f"checkpoint saved episode STL: mean={np.mean(ep_stl):.4f} "
          f"range=[{min(ep_stl):.3f},{max(ep_stl):.3f}]  "
          f"(rewards==stl fields: {fields_identical})")
    print(f"forward pass: probs_shape={fwd['action_probs_shape']} value={fwd['value_shape']} "
          f"latent={fwd['latent_shape']} probs_sum={fwd['probs_sum']:.3f}")
    print(f"\nevaluation (n={n_episodes} episodes, shared starts, grid 10x10, window [92,165]):")
    for k in ("trained_greedy", "trained_sampling", "random_policy"):
        b = eval_res[k]
        print(f"  {k:16s}: stl={b['mean_stl_robustness']:.4f} "
              f"shaped={b['mean_shaped_reward']:.2f} success(>=0.95)={b['success_rate_ge095']:.2f}")
    print(f"  trained_greedy - random STL gap = {eval_res['trained_greedy_vs_random_stl_gap']:.4f}")
    print(f"  trained_greedy - random shaped-reward gap = "
          f"{eval_res['trained_greedy_vs_random_shaped_gap']:.2f}")
    print("\ntrained policy action distribution (n=%d random observations):" % adist["n_samples"])
    print("  mean probs:", np.round(adist["mean_action_probs"], 3).tolist())
    print("  argmax counts:", adist["argmax_action_counts"],
          "-> dominant action", adist["argmax_dominant_action"])
    print(f"  mean entropy {adist['mean_entropy']:.3f} (max {adist['max_entropy_9_actions']:.3f})")
    print("\nSaved results/ -> c04_drl_agent.json")


if __name__ == "__main__":
    main()
