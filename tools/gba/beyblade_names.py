"""Build canonical names from the code-indexed complete-Beyblade table."""
from .beyblade_table import extract_records,read_c_string

def catalogue(rom:bytes):
 out=[]
 for r in extract_records(rom):
  names=[read_c_string(rom,p) for p in r.name_pointers]
  out.append({'canonical_index':r.index,'displayed_text':names[0],'localized_texts':names,'string_offset':r.name_pointers[0]-0x08000000,'runtime_string_address':r.name_pointers[0],'shared_across_languages':len(set(names))==1,'confidence':'confirmed'})
 return out
