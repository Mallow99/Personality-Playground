"""Remove a white source matte using the character's known three-color palette.

Changing alpha alone leaves white blended into the edge RGB. Estimate coverage
against each palette color, then unmix the white before storing straight RGBA.
"""

import numpy as np


def remove_white_matte(rgb, palette):
    pixels = rgb.astype(np.float32)
    colors = np.array([tuple(bytes.fromhex(color[1:])) for color in palette], dtype=np.float32)
    direction = 255 - colors
    distance = 255 - pixels
    coverage = np.clip(
        np.einsum("hwc,kc->hwk", distance, direction) / (direction * direction).sum(axis=1),
        0,
        1,
    )
    reconstructed = 255 - coverage[..., None] * direction
    error = ((pixels[:, :, None, :] - reconstructed) ** 2).sum(axis=3)
    choice = error.argmin(axis=2)
    alpha = np.take_along_axis(coverage, choice[..., None], axis=2)[..., 0]
    # Source paper has slight texture. It is not a faint translucent character.
    alpha[alpha < 0.08] = 0
    alpha[alpha > 0.98] = 1
    foreground = np.clip(
        (pixels - 255 * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-6), 0, 255
    )
    foreground[alpha == 0] = 0
    return np.dstack([foreground.round().astype("uint8"), (alpha * 255).round().astype("uint8")])


def remove_baseline_debris(rgba):
    """Remove tiny detached baseline caption remnants, never a connected limb."""
    from collections import deque

    result = rgba.copy()
    mask = result[:, :, 3] > 20
    seen = np.zeros(mask.shape, dtype=bool)
    height, width = mask.shape
    removed = 0
    for sy, sx in zip(*np.where(mask & (np.indices(mask.shape)[0] >= 420)), strict=True):
        if seen[sy, sx]:
            continue
        queue = deque([(sy, sx)])
        seen[sy, sx] = True
        component = []
        while queue:
            y, x = queue.popleft()
            component.append((y, x))
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
        ys, xs = zip(*component, strict=True)
        if len(component) <= 120 and min(ys) >= 420 and max(ys) - min(ys) <= 14:
            result[np.array(ys), np.array(xs)] = 0
            removed += len(component)
    return result, removed
