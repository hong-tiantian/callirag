import torch
print('cuda_available', torch.cuda.is_available())
m = torch.nn.Conv2d(3, 64, 3).cuda()
x = torch.randn(1, 3, 8, 8, device='cuda')
y = m(x)
print('ok', y.shape)
