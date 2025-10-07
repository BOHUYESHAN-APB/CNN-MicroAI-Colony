import importlib,sys
mods=[onnx
onnxruntime
onnxruntime_tools
onnxruntime.quantization
]
for
m
in
mods:
^try:
^except
import importlib
mods=['onnx','onnxruntime','onnxruntime_tools','onnxruntime.quantization']
for m in mods:
	try:
		importlib.import_module(m)
		print(m + ' OK')
	except Exception as e:
		print(m + ' MISSING or failed: ' + str(e))
