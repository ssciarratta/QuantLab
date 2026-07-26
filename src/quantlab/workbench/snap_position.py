"""Pure window-edge snap geometry (F82) — mirror of ``wm.js`` ``snapPosition``.

Snaps ``(x, y)`` to viewport edges when distance to an edge is strictly
less than ``threshold`` pixels (default 12). Left/top win over right/bottom
when both gaps qualify (near full-bleed windows).
"""

from __future__ import annotations

DEFAULT_SNAP_THRESHOLD_PX = 12


def snap_position(
    x: int,
    y: int,
    w: int,
    h: int,
    vw: int,
    vh: int,
    threshold: int = DEFAULT_SNAP_THRESHOLD_PX,
) -> tuple[int, int]:
    """Return snapped ``(x, y)`` for a window of size ``(w, h)`` in ``(vw, vh)``.

    Args:
        x: Window left in workspace coordinates.
        y: Window top in workspace coordinates.
        w: Window width (px).
        h: Window height (px).
        vw: Viewport / workspace width (px).
        vh: Viewport / workspace height (px).
        threshold: Snap distance in pixels (default 12). Distance to an edge
            strictly less than this value triggers snap.

    Returns:
        Snapped ``(x, y)`` integers.
    """
    nx = int(x)
    ny = int(y)
    ww = int(w)
    hh = int(h)
    view_w = int(vw)
    view_h = int(vh)
    thr = max(0, int(threshold))

    if nx < thr:
        nx = 0
    elif (view_w - (nx + ww)) < thr:
        nx = view_w - ww

    if ny < thr:
        ny = 0
    elif (view_h - (ny + hh)) < thr:
        ny = view_h - hh

    return nx, ny
