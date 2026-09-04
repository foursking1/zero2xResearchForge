"""Student network used for few-sample knowledge-distillation compression.

StudentNet is a compact VGG-like CNN (~2.4M params) vs the VGG-16 teacher
(~134M) -> a >50x parameter reduction.
"""
import torch.nn as nn


def _conv(c_in, c_out):
    return nn.Conv2d(c_in, c_out, kernel_size=3, padding=1)


class _Block(nn.Module):
    def __init__(self, c_in, c_out):
        super().__init__()
        self.c1 = _conv(c_in, c_out)
        self.b1 = nn.BatchNorm2d(c_out)
        self.c2 = _conv(c_out, c_out)
        self.b2 = nn.BatchNorm2d(c_out)
        self.relu = nn.ReLU(inplace=True)
        self.pool = nn.MaxPool2d(2, 2)

    def forward(self, x):
        x = self.relu(self.b1(self.c1(x)))
        x = self.pool(self.relu(self.b2(self.c2(x))))
        return x


class StudentNet(nn.Module):
    def __init__(self, num_classes=10, widths=(32, 64, 128, 256)):
        super().__init__()
        self.blocks = nn.ModuleList()
        c_in = 3
        for w in widths:
            self.blocks.append(_Block(c_in, w))
            c_in = w
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(widths[-1] * 2 * 2, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        for b in self.blocks:
            x = b(x)
        return self.head(x)


def count_params(net):
    return sum(p.numel() for p in net.parameters())


if __name__ == "__main__":
    n = StudentNet()
    print("StudentNet params:", count_params(n))
    print("VGG-16(B) params: 134.21M")
    print("ratio:", count_params(n) / 134_211_146)