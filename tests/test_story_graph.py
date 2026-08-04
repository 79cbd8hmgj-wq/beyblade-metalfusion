import pytest
from tools.gba.story_graph import *
def test_graph_refs_and_json():
 g={'nodes':[{'id':'a'},{'id':'b'}],'edges':[{'source':'a','target':'b'}]}; validate_graph(g); assert deterministic_json(g)==deterministic_json(g)
 with pytest.raises(ValueError): validate_graph({'nodes':[{'id':'a'}],'edges':[{'source':'a','target':'z'}]})
