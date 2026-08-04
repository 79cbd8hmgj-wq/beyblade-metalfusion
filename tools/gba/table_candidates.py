"""Fixed-stride candidate scoring helpers used by Task 2 reports/tests."""
STRIDES=(4,6,8,10,12,14,16,20,24,28,32,36,40,44,48,56,64)
def pointer_field_counts(data,start,count,stride,base=0x08000000):
 import struct
 if start<0 or count<0 or stride<=0 or start+count*stride>len(data): raise ValueError('candidate outside input')
 result={}
 for rel in range(0,stride-3,4):
  result[rel]=sum(base<=struct.unpack_from('<I',data,start+i*stride+rel)[0]<base+len(data) for i in range(count))
 return result
