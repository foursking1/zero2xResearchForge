"""Faithful device-enabled port of pyod 3.6.4's DeepSVDD.

pyod 3.6.4's DeepSVDD computes everything on the CPU (no `device` argument).
This module re-implements the *exact* pyod algorithm (same network, same
loss incl. the `w_d = 1e-6 * ||W||` regularizer and the Adam weight_decay,
same center initialisation, same best-epoch snapshot) but moves the tensors
onto the requested torch.device. On 'cpu' the math is identical to pyod's,
so results are equivalent; the port merely adds 'cuda' for speed.

Only the training/decision source of pyod 3.6.4 was adapted (MIT licence,
Zhao et al., PyOD).
"""

import copy

import numpy as np
import torch
import torch as th
from torch.utils.data import DataLoader, TensorDataset

from pyod.models.deep_svdd import InnerDeepSVDD
from pyod.models.base import BaseDetector
from sklearn.utils.validation import check_array

optimizer_dict = {
    "adam": th.optim.Adam,
    "sgd": th.optim.SGD,
    "adagrad": th.optim.Adagrad,
    "rmsprop": th.optim.RMSprop,
    "adadelta": th.optim.Adadelta,
    "adamw": th.optim.AdamW,
}


class DeepSVDDDevice(BaseDetector):
    """See pyod.models.deep_svdd.DeepSVDD (pyod 3.6.4), plus `device`."""

    def __init__(self, n_features, device="cpu", c=None, use_ae=False,
                 hidden_neurons=None, hidden_activation="relu",
                 output_activation="sigmoid", optimizer="adam", epochs=100,
                 batch_size=32, dropout_rate=0.2, l2_regularizer=0.5e-6,
                 validation_size=0.1, preprocessing=True, verbose=1,
                 random_state=None, contamination=0.1, learning_rate=1e-4,
                 **kwargs):
        super().__init__(contamination=contamination)
        self.n_features = n_features
        self.device = torch.device(device)
        self.c = c
        self.use_ae = use_ae
        self.hidden_neurons = hidden_neurons if hidden_neurons else [64, 32]
        self.hidden_activation = hidden_activation
        self.output_activation = output_activation
        self.optimizer = optimizer
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.dropout_rate = dropout_rate
        self.l2_regularizer = l2_regularizer
        self.validation_size = validation_size
        self.preprocessing = preprocessing
        self.verbose = verbose
        self.random_state = random_state
        self.model_ = None
        self.best_model_dict = None
        if self.random_state is not None:
            torch.manual_seed(self.random_state)
        self.kwargs = kwargs

    def fit(self, X, y=None):
        X = check_array(X)
        self._set_n_classes(y)
        self.n_samples_, self.n_features_ = X.shape[0], X.shape[1]

        if self.preprocessing:
            from sklearn.preprocessing import StandardScaler
            self.scaler_ = StandardScaler()
            X_norm = self.scaler_.fit_transform(X)
        else:
            X_norm = np.copy(X)

        np.random.shuffle(X_norm)

        if np.min(self.hidden_neurons) > self.n_features_ and self.use_ae:
            raise ValueError(
                "The number of neurons should not exceed the number of features")

        self.model_ = InnerDeepSVDD(self.n_features, use_ae=self.use_ae,
                                    hidden_neurons=self.hidden_neurons,
                                    hidden_activation=self.hidden_activation,
                                    output_activation=self.output_activation,
                                    dropout_rate=self.dropout_rate,
                                    l2_regularizer=self.l2_regularizer)
        self.model_.to(self.device)

        X_t = torch.tensor(X_norm, dtype=torch.float32, device=self.device)
        if self.c is None:
            center = self.model_._init_c(X_t)
        else:
            center = torch.as_tensor(self.c, dtype=X_t.dtype, device=self.device)

        output_width = self.n_features if self.use_ae else self.hidden_neurons[-1]
        if center.ndim == 0:
            center = center.repeat(output_width)
        elif center.ndim != 1 or center.numel() != output_width:
            raise ValueError(
                f"DeepSVDD: c must be a scalar or a vector of length "
                f"{output_width}, got shape {tuple(center.shape)}.")
        if not torch.isfinite(center).all():
            raise ValueError("DeepSVDD: c must contain only finite values.")
        if not torch.any(center != 0):
            raise ValueError(
                "DeepSVDD: the hypersphere center is all zeros, which makes "
                "the trivial all-zero-weights solution optimal and collapses "
                "the hypersphere. Pass c=None to initialize the center from "
                "the data, or supply a non-zero center.")
        self.c_ = center.detach().clone()

        if self.preprocessing:
            X_norm = self.scaler_.transform(X)
        else:
            X_norm = np.copy(X)

        X_t = torch.tensor(X_norm, dtype=torch.float32, device=self.device)
        dataset = TensorDataset(X_t, X_t)
        dataloader = DataLoader(dataset, batch_size=self.batch_size,
                                shuffle=True)

        best_loss = float("inf")
        best_model_dict = None
        optimizer = optimizer_dict[self.optimizer](
            self.model_.parameters(), lr=self.learning_rate,
            weight_decay=self.l2_regularizer)

        for epoch in range(self.epochs):
            self.model_.train()
            epoch_loss = 0
            for batch_x, _ in dataloader:
                optimizer.zero_grad()
                outputs = self.model_(batch_x)
                dist = torch.sum((outputs - self.c_) ** 2, dim=-1)
                w_d = 1e-6 * sum(
                    [torch.linalg.norm(w) for w in self.model_.parameters()])
                if self.use_ae:
                    loss = torch.mean(dist) + w_d + torch.mean(
                        torch.square(outputs - batch_x))
                else:
                    loss = torch.mean(dist) + w_d
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            if epoch_loss < best_loss:
                best_loss = epoch_loss
                best_model_dict = copy.deepcopy(self.model_.state_dict())
            if self.verbose:
                print(f"Epoch {epoch + 1}/{self.epochs}, Loss: {epoch_loss}")
        self.best_model_dict = best_model_dict
        if self.best_model_dict is not None:
            self.model_.load_state_dict(self.best_model_dict)

        # decision_scores_ computed on train set (self-evaluation, pyod parity)
        self.decision_scores_ = self.decision_function(X)
        self._process_decision_scores()
        return self

    def decision_function(self, X):
        X = check_array(X)
        if self.preprocessing:
            X_norm = self.scaler_.transform(X)
        else:
            X_norm = np.copy(X)
        X_t = torch.tensor(X_norm, dtype=torch.float32, device=self.device)
        self.model_.eval()
        with torch.no_grad():
            outputs = self.model_(X_t)
            dist = torch.sum((outputs - self.c_) ** 2, dim=-1)
        return dist.detach().cpu().numpy()