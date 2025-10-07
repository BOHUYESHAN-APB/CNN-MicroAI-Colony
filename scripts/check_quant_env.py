import importlib
modules = ['onnx','onnxruntime','onnxruntime.quantization']
for m in modules:
    try:
        importlib.import_module(m)
        print(m + ' OK')
    except Exception as e:
        print(m + ' MISSING or failed: ' + str(e))
