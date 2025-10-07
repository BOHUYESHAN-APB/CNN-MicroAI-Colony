import torch
import os
import sys

paths = [r'd:\train\faster_rcnn_colony_epoch12.pth', r'd:\train\checkpoint_epoch_31.pth']
for p in paths:
    print('---', p)
    if not os.path.exists(p):
        print('MISSING')
        continue
    try:
        data = torch.load(p, map_location='cpu')
        print('TYPE:', type(data))
        if isinstance(data, dict):
            print('keys:', list(data.keys())[:50])
            if 'meta' in data:
                m = data['meta']
                print('meta type:', type(m))
            mm_keys = [k for k in data.keys() if any(x in k for x in ['state_dict','model','optimizer','meta'])]
            print('possible mm det keys:', mm_keys)
        else:
            print('not a dict, class:', data.__class__)
    except Exception as e:
        print('ERROR reading:', e)

print('\nDone')
