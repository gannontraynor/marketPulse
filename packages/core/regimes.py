from typing import Optional

def regime_from_vol(
    vol_ann: float,
    vol_percentile_1y: Optional[float],
) -> str:
    """
    Returns a stable regime label.
    Priority: percentile (relative) when available, else absolute fallback.
    """
    if vol_percentile_1y is not None:
        if vol_percentile_1y >= 0.90:
            return "VOL_SPIKE"
        if vol_percentile_1y >= 0.80:
            return "VOL_ELEVATED"
        if vol_percentile_1y <= 0.10:
            return "VOL_CRUSH"
        return "NORMAL"

    # fallback (if percentile can't be computed)
    if vol_ann >= 0.50:
        return "ABS_HIGH_VOL"
    if vol_ann <= 0.10:
        return "ABS_LOW_VOL"
    return "NORMAL"