import torch, torch.nn as nn, time
torch.set_num_threads(20)

def conv3(in_c, out_c, stride=1):
    return nn.Conv2d(in_c, out_c, 3, stride, 1, bias=False)

class Block(nn.Module):
    def __init__(self, in_c, out_c, stride=1):
        super().__init__()
        self.c1 = conv3(in_c, out_c, stride)
        self.b1 = nn.BatchNorm2d(out_c)
        self.c2 = conv3(out_c, out_c)
        self.b2 = nn.BatchNorm2d(out_c)
        self.short = nn.Sequential()
        if stride != 1 or in_c != out_c:
            self.short = nn.Sequential(nn.Conv2d(in_c, out_c, 1, stride), nn.BatchNorm2d(out_c))
    def forward(self, x):
        h = torch.relu(self.b1(self.c1(x)))
        h = self.b2(self.c2(h))
        return torch.relu(h + self.short(x))

class MiniResNet(nn.Module):
    def __init__(self, in_ch=10, nclass=17, w=32):
        super().__init__()
        self.g = nn.Sequential(
            nn.Conv2d(in_ch, w, 3, 1, 1, bias=False), nn.BatchNorm2d(w), nn.ReLU(),
            Block(w, w), Block(w, w),
            Block(w, 2*w, 2), Block(2*w, 2*w),
            Block(2*w, 4*w, 2), Block(4*w, 4*w),
            nn.AdaptiveAvgPool2d(1),
        )
        self.fc = nn.Linear(4*w, nclass)
    def forward(self, x):
        h = self.g(x).flatten(1)
        return self.fc(h)

x = torch.randn(64, 10, 32, 32)
model = MiniResNet(in_ch=10, w=32)
criterion = nn.CrossEntropyLoss()
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
start = time.time()
for it in range(20):
    opt.zero_grad()
    out = model(x)
    loss = criterion(out, torch.randint(0, 17, (64,)))
    loss.backward()
    opt.step()
elapsed = time.time() - start
print(f"CPU: {(elapsed/20)*1000:.0f} ms/step (batch 64), param count {sum(p.numel() for p in model.parameters())/1e6:.2f}M")