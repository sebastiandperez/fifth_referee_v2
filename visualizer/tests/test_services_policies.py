from domain.services.policies import PointsPolicy, TieBreakPolicy

def test_points_policy_defaults_and_customization():
    p = PointsPolicy()
    assert p.points(2,1) == 3
    assert p.points(1,1) == 1
    assert p.points(0,2) == 0
    p2 = PointsPolicy(points_for_win=2, points_for_draw=0, points_for_loss=0)
    assert p2.points(5,4) == 2
    assert p2.points(1,1) == 0

def test_tiebreak_key_orders_pts_gd_gf_desc():
    tb = TieBreakPolicy()
    rows = [(10,5,12,1), (10,5,8,2), (9,20,50,3)]
    ordered = sorted(rows, key=lambda r: tb.compare_key(*r))
    assert ordered[0][:3] == (10,5,12)
    assert ordered[1][:3] == (10,5,8)
    assert ordered[2][:3] == (9,20,50)
