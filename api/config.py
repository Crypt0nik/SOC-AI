"""Plan and feature-flag configuration for SOC-AI."""

import os

PLAN: str = os.environ.get("PLAN", "community").lower()
ADMIN_TOKEN: str = os.environ.get("ADMIN_TOKEN", "")

PRO_FEATURES: set[str] = {"webhooks", "mitre_heatmap", "risk_scores", "compliance"}
ENTERPRISE_FEATURES: set[str] = PRO_FEATURES | {"multi_tenant", "sso", "nis2_report"}


def is_pro() -> bool:
    """Return True when the current plan includes Pro features."""
    return PLAN in ("pro", "enterprise")


def is_enterprise() -> bool:
    """Return True when the current plan is Enterprise."""
    return PLAN == "enterprise"


def has_feature(name: str) -> bool:
    """Return True if *name* is available on the current plan.

    Args:
        name: Feature key (e.g. ``"mitre_heatmap"``).

    Returns:
        Whether the feature is available.
    """
    if PLAN == "enterprise":
        return name in ENTERPRISE_FEATURES
    if PLAN == "pro":
        return name in PRO_FEATURES
    return False


def enabled_features() -> list[str]:
    """Return the list of feature keys enabled on the current plan.

    Returns:
        Sorted list of feature key strings.
    """
    if PLAN == "enterprise":
        return sorted(ENTERPRISE_FEATURES)
    if PLAN == "pro":
        return sorted(PRO_FEATURES)
    return []
