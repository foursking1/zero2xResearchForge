"""Model factory and layer helpers (ResNet-18, random init)."""
import torch
import torch.nn as nn
from torchvision.models import resnet18

from config import set_seed


def make_resnet18(num_classes=2, seed=42):
    set_seed(seed)
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


# Paper layer numbering (Appendix A):
#   1: conv1, 2: bn1+relu, 3: maxpool, 4..11: basic blocks,
#   12: avgpool, 13: linear
def _flatten_layers(model):
    layers = [model.conv1]
    layers.append(nn.Sequential(model.bn1, model.relu))
    layers.append(model.maxpool)
    layers += [b for b in model.layer1] + [b for b in model.layer2]
    layers += [b for b in model.layer3] + [b for b in model.layer4]
    layers.append(model.avgpool)
    layers.append(model.fc)
    return layers


def get_layer(model, l):
    """Return module at paper layer index l (1..13)."""
    return _flatten_layers(model)[l - 1]


def hook_activation(model, l):
    """Register forward hook returning the post-activation of layer l.

    Returns (handle, forward_activations_list).
    """
    act = {}

    def fn(m, i, o):
        act["val"] = o.detach()

    handle = get_layer(model, l).register_forward_hook(fn)
    return handle, act


def num_trainable(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
