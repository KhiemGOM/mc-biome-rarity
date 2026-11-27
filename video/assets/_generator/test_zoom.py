"""Framing for the V007 push-ins. Run: python -m pytest -q test_zoom.py (from this folder)."""
from zoom import frame_box, lerp_box, ease

W, H = 3840, 2160


def aspect(b):
    return (b[2] - b[0]) / (b[3] - b[1])


def inside(inner, outer, tol=1e-6):
    return inner[0] >= outer[0] - tol and inner[1] >= outer[1] - tol and inner[2] <= outer[2] + tol and inner[3] <= outer[3] + tol


def test_crop_is_16_by_9_and_holds_the_claim():
    claim = (1290, 864, 2092, 904)
    b = frame_box(claim, W, H)
    assert abs(aspect(b) - 16 / 9) < 1e-6 and inside(claim, b)


def test_claim_fills_the_asked_share_of_the_width():
    claim = (1500, 1000, 2100, 1040)  # 600 wide
    b = frame_box(claim, W, H, fill=0.6, max_zoom=10)
    assert abs((b[2] - b[0]) - 1000) < 1e-6


def test_claim_is_centred_when_there_is_room():
    claim = (1500, 1000, 2100, 1040)
    b = frame_box(claim, W, H, fill=0.6, max_zoom=10)
    assert abs((b[0] + b[2]) / 2 - 1800) < 1e-6 and abs((b[1] + b[3]) / 2 - 1020) < 1e-6


def test_crop_near_an_edge_is_clamped_inside_the_image():
    b = frame_box((10, 2100, 300, 2150), W, H)
    assert inside(b, (0, 0, W, H)) and inside((10, 2100, 300, 2150), b)


def test_tiny_claim_is_not_zoomed_past_the_limit():
    b = frame_box((1900, 1000, 1960, 1020), W, H, fill=0.6, max_zoom=3)
    assert abs((b[2] - b[0]) - W / 3) < 1e-6


def test_huge_claim_never_zooms_out_past_the_full_image():
    b = frame_box((0, 0, W, H), W, H)
    assert b == (0, 0, W, H)


def test_tall_claim_is_fitted_by_height_too():
    claim = (1800, 500, 1900, 1500)  # 1000 tall, thin
    b = frame_box(claim, W, H, fill=0.6, max_zoom=10)
    assert inside(claim, b) and abs(aspect(b) - 16 / 9) < 1e-6


def test_lerp_starts_full_and_ends_on_target():
    full, tgt = (0, 0, W, H), (1000, 500, 1960, 1040)
    assert lerp_box(full, tgt, 0) == full and lerp_box(full, tgt, 1) == tgt


def test_ease_is_smooth_and_clamped():
    assert ease(-1) == 0 and ease(0) == 0 and ease(1) == 1 and ease(2) == 1 and abs(ease(0.5) - 0.5) < 1e-9
