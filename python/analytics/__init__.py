"""
NovaNest Advanced Business Analytics & Decision Intelligence Package
Contains modular engines for RFM segmentation, monthly cohort retention,
marketing funnel conversion, core KPI calculation, and cross-validation.
"""

from .rfm_segmentation import calculate_rfm_segments
from .cohort_analysis import compute_cohort_retention_matrix
from .funnel_analysis import analyze_marketing_funnel
from .kpi_engine import compute_all_kpis
from .validate_kpis import run_cross_validation

__all__ = [
    "calculate_rfm_segments",
    "compute_cohort_retention_matrix",
    "analyze_marketing_funnel",
    "compute_all_kpis",
    "run_cross_validation"
]

