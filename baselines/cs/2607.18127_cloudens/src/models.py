"""Model backbones for ClouDens reproduction.

GRU baseline (no graph) and the A3T-GCN based ClouDens model, both with an
identical single-shot next-step forecasting interface (slide_win -> next step,
w=6), Adam lr=1e-3, MSE loss, batch 32, and a 32-unit hidden layer.

The A3T-GCN cell (TGCN2 / A3TGCN2) is copied from the official reproduction
package (torch-geometric-temporal, bundled under _pgt_repo/).  The temporal
GNN wrapper (input permutation + attention cell + relu + linear + sigmoid) and
the GRU baseline mirror src/model_wrappers/GRUWrapper.py and A3TGCNWrapper.py
of the paper's reproduction repository.
"""
import time

import numpy as np
import torch

from tgnn_attentiontemporalgcn import A3TGCN2


# --------------------------------------------------------------------------
# GRU baseline
# --------------------------------------------------------------------------
class GRUCustom(torch.nn.Module):
    def __init__(self, num_nodes, node_features, hidden_dim, layer_dim, dropout=0.3):
        super(GRUCustom, self).__init__()
        self.num_nodes = num_nodes
        self.node_features = node_features
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        self.in_dim = num_nodes * node_features
        self.rnn = torch.nn.GRU(input_size=self.in_dim,
                                hidden_size=hidden_dim,
                                num_layers=layer_dim,
                                dropout=dropout,
                                batch_first=True)
        self.linear = torch.nn.Linear(hidden_dim, self.in_dim)

    def forward(self, x):
        # x: [B, slide_win, num_nodes, node_feat]
        B, T, N, F = x.shape
        x = x.reshape(B, T, -1)
        h0 = torch.zeros(self.layer_dim, B, self.hidden_dim, device=x.device)
        out, _ = self.rnn(x, h0)
        out = self.linear(out[:, -1, :])
        return out.reshape(B, N, F)


class GRUWrapper:
    """Same train/predict interface as the reference GRUWrapper."""

    def __init__(self, num_nodes, node_features, hidden_dim=32, layer_dim=1,
                 batch_size=32, device="cpu", lr=1e-3):
        self.device = device
        self.num_nodes = num_nodes
        self.node_features = node_features
        self.batch_size = batch_size
        self.model = GRUCustom(num_nodes, node_features, hidden_dim, layer_dim).to(device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.loss_fn = torch.nn.MSELoss()
        self.inference_time = 0.0

    def train(self, train_loader, val_loader, epochs):
        model = self.model
        train_losses, valid_losses = [], []
        t0 = time.time()
        for epoch in range(epochs):
            model.train()
            loss_list = []
            for xb, yb in train_loader:
                xb, yb = xb.to(self.device), yb.to(self.device)
                y_hat = model(xb)
                loss = self.loss_fn(y_hat, yb)
                loss.backward()
                self.optimizer.step()
                self.optimizer.zero_grad()
                loss_list.append(loss.item())
            epoch_train_loss = float(np.mean(loss_list))
            preds, _, _, epoch_valid_loss = self.predict(val_loader, mode="valid")
            valid_losses.append(epoch_valid_loss)
            train_losses.append(epoch_train_loss)
            print(f"Epoch {epoch} train RMSE: {epoch_train_loss:.7f}, valid RMSE: {epoch_valid_loss:.7f}")
        history = dict(epochs=epochs, train_losses=train_losses,
                       valid_losses=valid_losses, training_time=time.time() - t0)
        return history

    @torch.no_grad()
    def predict(self, test_loader, mode="test"):
        self.model.eval()
        total_loss, recon_err, preds = [], [], []
        t0 = time.time()
        for xb, yb in test_loader:
            xb, yb = xb.to(self.device), yb.to(self.device)
            y_hat = self.model(xb)
            preds.append(y_hat.cpu().numpy())
            total_loss.append(self.loss_fn(y_hat, yb).item())
            recon_err.append(torch.abs(y_hat - yb).cpu().numpy())
        recon_err = np.concatenate(recon_err, axis=0)
        preds = np.concatenate(preds, axis=0)
        self.inference_time = time.time() - t0
        return preds, None, recon_err, float(np.mean(total_loss))


# --------------------------------------------------------------------------
# ClouDens: A3T-GCN + operational-context graph
# --------------------------------------------------------------------------
class TemporalGNN(torch.nn.Module):
    def __init__(self, node_features, periods, batch_size):
        super(TemporalGNN, self).__init__()
        self.tgnn = A3TGCN2(in_channels=node_features, out_channels=32,
                            periods=periods, batch_size=batch_size)
        self.linear = torch.nn.Linear(32, node_features)
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x, edge_index, edge_weight):
        # x: [B, slide_win, num_nodes, node_feat]
        x = x.permute(0, 2, 3, 1)                # [B, num_nodes, node_feat, slide_win]
        h = self.tgnn(x, edge_index, edge_weight)  # [B, num_nodes, 32]
        h = torch.relu(h)
        h = self.linear(h)                        # [B, num_nodes, node_feat]
        h = self.sigmoid(h)
        return h


class A3TGCNWrapper:
    def __init__(self, node_features, periods, edge_index, edge_weight,
                 batch_size=32, device="cpu", lr=1e-3):
        self.device = device
        self.edge_index = edge_index
        self.edge_weight = edge_weight
        self.node_features = node_features
        self.periods = periods
        self.batch_size = batch_size
        self.model = TemporalGNN(node_features, periods, batch_size).to(device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.loss_fn = torch.nn.MSELoss()
        self.inference_time = 0.0

    def train(self, train_loader, val_loader, epochs):
        model = self.model
        train_losses, valid_losses = [], []
        t0 = time.time()
        for epoch in range(epochs):
            model.train()
            loss_list = []
            for xb, yb in train_loader:
                xb, yb = xb.to(self.device), yb.to(self.device)
                y_hat = model(xb, self.edge_index, self.edge_weight)
                loss = self.loss_fn(y_hat, yb)
                loss.backward()
                self.optimizer.step()
                self.optimizer.zero_grad()
                loss_list.append(loss.item())
            epoch_train_loss = float(np.mean(loss_list))
            preds, _, _, epoch_valid_loss = self.predict(val_loader, mode="valid")
            valid_losses.append(epoch_valid_loss)
            train_losses.append(epoch_train_loss)
            print(f"Epoch {epoch} train RMSE: {epoch_train_loss:.7f}, valid RMSE: {epoch_valid_loss:.7f}")
        history = dict(epochs=epochs, train_losses=train_losses,
                       valid_losses=valid_losses, training_time=time.time() - t0)
        return history

    @torch.no_grad()
    def predict(self, test_loader, mode="test"):
        self.model.eval()
        total_loss, recon_err, preds = [], [], []
        t0 = time.time()
        for xb, yb in test_loader:
            xb, yb = xb.to(self.device), yb.to(self.device)
            y_hat = self.model(xb, self.edge_index, self.edge_weight)
            y_hat_np = y_hat.cpu().numpy()
            yb_np = yb.cpu().numpy()
            preds.append(y_hat_np[:, :, 0])
            total_loss.append(self.loss_fn(y_hat, yb).item())
            recon_err.append(np.abs(y_hat_np - yb_np)[:, :, 0:1])
        recon_err = np.concatenate(recon_err, axis=0)   # [T, num_nodes, 1]
        preds = np.concatenate(preds, axis=0)           # [T, num_nodes]
        self.inference_time = time.time() - t0
        return preds, None, recon_err, float(np.mean(total_loss))