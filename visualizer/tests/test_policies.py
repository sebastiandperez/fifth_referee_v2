import pytest
from domain.services.policies import PointsPolicy, TieBreakPolicy

def test_points_policy_default_3_1_0():
    pol = PointsPolicy()
    assert pol.points(2, 1) == 3   # win
    assert pol.points(1, 1) == 1   # draw
    assert pol.points(0, 2) == 0   # loss

def test_points_policy_customizable():
    pol = PointsPolicy(points_for_win=2, points_for_draw=1, points_for_loss=0)
    assert pol.points(4, 0) == 2
    assert pol.points(0, 0) == 1
    assert pol.points(0, 5) == 0

def test_tiebreak_default_orders_pts_then_gd_then_gf():
    tb = TieBreakPolicy()
    rows = [
        (10,  5, 12, 1),  # same Pts/GD as next, more GF => first
        (10,  5,  8, 2),
        ( 9, 10, 20, 3),
    ]
    ordered = sorted(rows, key=lambda r: tb.compare_key(*r))
    assert ordered[0][:3] == (10, 5, 12)
    assert ordered[1][:3] == (10, 5, 8)
    assert ordered[2][:3] == (9, 10, 20)
