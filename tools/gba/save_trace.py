"""Emit reproducible debugger breakpoint addresses for Task 5."""
import json
BREAKPOINTS=[0x080674bc,0x08044a8c,0x08067584,0x08044fb0,0x0804504c,0x080450e4,0x08045590,0x08044dac,0x08044e54,0x08044ea0,0x08044f14,0x08044d2c,0x08067634,0x080677a8]
def report():return {'status':'not_run','reason':'interactive save-capable session unavailable','breakpoints':[f'0x{x:08X}' for x in BREAKPOINTS]}
if __name__=='__main__':print(json.dumps(report(),indent=2))
