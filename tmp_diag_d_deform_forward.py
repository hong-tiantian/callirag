import torch
from torchvision.ops import DeformConv2d
m = DeformConv2d(3, 8, kernel_size=3, padding=1)
x = torch.randn(1, 3, 8, 8)
offset = torch.randn(1, 18, 8, 8)
y = m(x, offset)
print('ok', y.shape)
