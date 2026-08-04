from tools.gba.progression_system import saturating_experience
def test_saturation(): assert saturating_experience(90,20,100)==100
