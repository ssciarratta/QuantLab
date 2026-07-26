"""Pure cascade / tile window geometry (F84) — mirror of ``wm.js`` helpers.

Computes ``(x, y, w, h)`` rects for ``n`` windows inside a viewport
``(vw, vh)``. Used by unit tests; JS ``cascadeRects`` / ``tileRects``
drive the live window manager.
"""

from __future__ import annotations

from typing import TypedDict

DEFAULT_CASCADE_OFFSET_PX = 28
DEFAULT_CASCADE_BASE_X = 24
DEFAULT_CASCADE_BASE_Y = 24
DEFAULT_CASCADE_WIN_W = 420
DEFAULT_CASCADE_WIN_H = 320
DEFAULT_TILE_GAP_PX = 4
DEFAULT_TILE_MARGIN_PX = 4
MIN_WIN_W = 280
MIN_WIN_H = 180


class WindowRect(TypedDict):
    """Axis-aligned window rectangle in workspace coordinates."""

    x: int
    y: int
    w: int
    h: int


def cascade_rects(
    n: int,
    vw: int,
    vh: int,
    *,
    offset: int = DEFAULT_CASCADE_OFFSET_PX,
    base_x: int = DEFAULT_CASCADE_BASE_X,
    base_y: int = DEFAULT_CASCADE_BASE_Y,
    win_w: int = DEFAULT_CASCADE_WIN_W,
    win_h: int = DEFAULT_CASCADE_WIN_H,
) -> list[WindowRect]:
    """Return ``n`` cascaded rects (diagonal offset, wrap when off-screen).

    Args:
        n: Number of windows (``n <= 0`` → empty list).
        vw: Viewport width (px).
        vh: Viewport height (px).
        offset: Diagonal step between successive windows.
        base_x: Cascade origin x.
        base_y: Cascade origin y.
        win_w: Window width (clamped to viewport and ``MIN_WIN_W``).
        win_h: Window height (clamped to viewport and ``MIN_WIN_H``).

    Returns:
        List of ``{x, y, w, h}`` dicts in cascade order.
    """
    count = max(0, int(n))
    if count == 0:
        return []

    view_w = max(1, int(vw))
    view_h = max(1, int(vh))
    step = max(1, int(offset))
    origin_x = max(0, int(base_x))
    origin_y = max(0, int(base_y))
    width = max(MIN_WIN_W, min(int(win_w), view_w))
    height = max(MIN_WIN_H, min(int(win_h), view_h))

    # Keep at least one cascade step visible inside the viewport.
    max_x = max(0, view_w - width)
    max_y = max(0, view_h - height)
    wrap_x = max(origin_x, max_x)
    wrap_y = max(origin_y, max_y)

    rects: list[WindowRect] = []
    cx = origin_x
    cy = origin_y
    for _ in range(count):
        if cx > max_x or cy > max_y:
            cx = origin_x
            cy = origin_y
        rects.append({"x": cx, "y": cy, "w": width, "h": height})
        cx += step
        cy += step
        if cx > wrap_x and cy > wrap_y:
            cx = origin_x
            cy = origin_y
    return rects


def tile_rects(
    n: int,
    vw: int,
    vh: int,
    *,
    gap: int = DEFAULT_TILE_GAP_PX,
    margin: int = DEFAULT_TILE_MARGIN_PX,
) -> list[WindowRect]:
    """Return ``n`` tiled rects in a near-square grid covering the viewport.

    Args:
        n: Number of windows (``n <= 0`` → empty list).
        vw: Viewport width (px).
        vh: Viewport height (px).
        gap: Gap between cells (px).
        margin: Outer margin from viewport edges (px).

    Returns:
        List of ``{x, y, w, h}`` dicts in row-major order.
        Cell sizes are at least ``MIN_WIN_W`` × ``MIN_WIN_H`` when the
        viewport allows; otherwise they shrink to fit.
    """
    count = max(0, int(n))
    if count == 0:
        return []

    view_w = max(1, int(vw))
    view_h = max(1, int(vh))
    cell_gap = max(0, int(gap))
    outer = max(0, int(margin))

    cols = int(count**0.5)
    if cols * cols < count:
        cols += 1
    if cols < 1:
        cols = 1
    rows = (count + cols - 1) // cols

    avail_w = max(1, view_w - 2 * outer - (cols - 1) * cell_gap)
    avail_h = max(1, view_h - 2 * outer - (rows - 1) * cell_gap)
    cell_w = max(1, avail_w // cols)
    cell_h = max(1, avail_h // rows)

    rects: list[WindowRect] = []
    for i in range(count):
        row = i // cols
        col = i % cols
        x = outer + col * (cell_w + cell_gap)
        y = outer + row * (cell_h + cell_gap)
        rects.append({"x": x, "y": y, "w": cell_w, "h": cell_h})
    return rects
