import torch
m = torch.nn.Conv2d(3, 64, 3)
x = torch.randn(1, 3, 8, 8)
y = m(x)
print('ok', y.shape)
