import torch
import os
import traceback

paths = [r'd:\train\faster_rcnn_colony_epoch12.pth', r'd:\train\checkpoint_epoch_31.pth']

def try_load(path):
    try:
        return torch.load(path, map_location='cpu')
    except TypeError:
        # older torch versions don't support weights_only arg; try without
        raise
    except Exception as e:
        print('First load failed:', e)
        # try weights_only=False if supported
        try:
            return torch.load(path, map_location='cpu', weights_only=False)
        except Exception as e2:
            print('Second load failed:', e2)
            # try safe globals
            try:
                from torch.serialization import add_safe_globals
                with add_safe_globals([getattr]):
                    return torch.load(path, map_location='cpu')
            except Exception as e3:
                print('Third load failed:', e3)
                print('Traceback:')
                traceback.print_exc()
                return None

for p in paths:
    print('\n---', p)
    if not os.path.exists(p):
        print('MISSING')
        continue
    data = try_load(p)
    if data is None:
        print('Could not load checkpoint')
        continue
    print('Loaded type:', type(data))
    if isinstance(data, dict):
        keys = list(data.keys())
        print('Top keys:', keys[:50])
        if 'model_state_dict' in data:
            sd = data['model_state_dict']
        elif 'state_dict' in data:
            sd = data['state_dict']
        elif 'model' in data and isinstance(data['model'], dict):
            sd = data['model']
        else:
            sd = None

        if sd is not None:
            print('State dict type:', type(sd), 'num params:', len(sd))
            sample_keys = list(sd.keys())[:30]
            print('Sample state_dict keys:', sample_keys)
        # print meta if available
        if 'meta' in data:
            print('meta keys:', list(data['meta'].keys()) if isinstance(data['meta'], dict) else type(data['meta']))
    else:
        print('Checkpoint is not dict: class', type(data))

print('\nDone')
