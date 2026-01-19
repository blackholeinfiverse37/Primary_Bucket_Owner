"""
Scale Limits and Performance Targets
Based on doc 15 - SCALE_READINESS.md
"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ScaleLimits:
    """
    Enterprise-grade scale limits for BHIV Bucket.
    These limits are ENFORCED, not suggested.
    """
    
    # Throughput limits
    WRITES_PER_SECOND_LIMIT = 1_000          # Verified under load
    READS_PER_SECOND_LIMIT = 10_000          # Verified under load
    BATCH_OPERATION_MAX_ITEMS = 10_000       # Per batch
    
    # Storage limits
    MAX_ARTIFACTS = 100_000_000              # Safe capacity
    MAX_ARTIFACT_SIZE = 500_000_000          # 500MB per artifact
    MAX_COLLECTION_SIZE = 10_000_000_000_000 # 10TB total
    
    # Latency targets (p95)
    FETCH_LATENCY_TARGET_MS = 100            # Single artifact
    LIST_LATENCY_TARGET_MS = 500             # List query
    WRITE_LATENCY_TARGET_MS = 200            # Write operation
    
    # Connection limits
    MAX_CONCURRENT_CONNECTIONS = 1_000
    CONNECTION_POOL_SIZE = 100
    CONNECTION_TIMEOUT_SECONDS = 30
    
    # What scales safely
    SCALES_SAFELY = [
        "read_heavy_workloads",
        "time_distributed_writes",
        "archive_queries",
        "metadata_searches"
    ]
    
    # What does NOT scale yet
    DOES_NOT_SCALE = [
        "real_time_concurrent_writes_same_artifact",
        "full_text_search_all_artifacts",
        "complex_joins_across_types",
        "geo_distributed_consistency"
    ]
    
    # Assumptions that must NEVER be made
    NEVER_ASSUME = [
        "eventual_consistency_is_guaranteed",  # NO - sync model only
        "artifacts_can_be_quietly_deleted",    # NO - 90-day window
        "schema_changes_backward_compatible",  # NO - breaking changes allowed
        "any_team_can_write_directly",         # NO - approval only
        "immutability_is_automatic",           # NO - must be enforced
        "provenance_is_complete"               # NO - can have gaps (Phase 1)
    ]

@dataclass
class PerformanceTargets:
    """Performance SLA targets for enterprise."""
    
    # Percentile targets
    P50_LATENCY_MS = 30
    P95_LATENCY_MS = 100
    P99_LATENCY_MS = 500
    
    # Error rates
    MAX_ERROR_RATE_PERCENT = 0.1  # 0.1% max
    
    # Availability
    MINIMUM_UPTIME_PERCENT = 99.5  # 99.5% SLA


def validate_operation_scale(
    operation_type: str,
    data_size: int,
    frequency: int
) -> tuple[bool, Optional[str]]:
    """
    Validate if operation is within scale limits.
    
    Args:
        operation_type: Type of operation (read/write)
        data_size: Size of data in bytes
        frequency: Operations per second
    
    Returns:
        (is_valid, error_message)
    """
    
    limits = ScaleLimits()
    
    # Check data size
    if data_size > limits.MAX_ARTIFACT_SIZE:
        return False, f"Artifact size {data_size} exceeds {limits.MAX_ARTIFACT_SIZE} limit"
    
    # Check frequency
    if operation_type == "write" and frequency > limits.WRITES_PER_SECOND_LIMIT:
        return False, f"Write frequency {frequency}/s exceeds {limits.WRITES_PER_SECOND_LIMIT}/s limit"
    
    if operation_type == "read" and frequency > limits.READS_PER_SECOND_LIMIT:
        return False, f"Read frequency {frequency}/s exceeds {limits.READS_PER_SECOND_LIMIT}/s limit"
    
    return True, None


def get_scale_limits_dict() -> dict:
    """Get scale limits as dictionary for API responses"""
    limits = ScaleLimits()
    return {
        "throughput": {
            "writes_per_second": limits.WRITES_PER_SECOND_LIMIT,
            "reads_per_second": limits.READS_PER_SECOND_LIMIT,
            "batch_max_items": limits.BATCH_OPERATION_MAX_ITEMS
        },
        "storage": {
            "max_artifacts": limits.MAX_ARTIFACTS,
            "max_artifact_size": limits.MAX_ARTIFACT_SIZE,
            "max_collection_size": limits.MAX_COLLECTION_SIZE
        },
        "latency_targets_ms": {
            "fetch_p95": limits.FETCH_LATENCY_TARGET_MS,
            "list_p95": limits.LIST_LATENCY_TARGET_MS,
            "write_p95": limits.WRITE_LATENCY_TARGET_MS
        },
        "connections": {
            "max_concurrent": limits.MAX_CONCURRENT_CONNECTIONS,
            "pool_size": limits.CONNECTION_POOL_SIZE,
            "timeout_seconds": limits.CONNECTION_TIMEOUT_SECONDS
        },
        "scales_safely": limits.SCALES_SAFELY,
        "does_not_scale": limits.DOES_NOT_SCALE,
        "never_assume": limits.NEVER_ASSUME
    }


def get_performance_targets_dict() -> dict:
    """Get performance targets as dictionary for API responses"""
    targets = PerformanceTargets()
    return {
        "latency_ms": {
            "p50": targets.P50_LATENCY_MS,
            "p95": targets.P95_LATENCY_MS,
            "p99": targets.P99_LATENCY_MS
        },
        "error_rate": {
            "max_percent": targets.MAX_ERROR_RATE_PERCENT
        },
        "availability": {
            "minimum_uptime_percent": targets.MINIMUM_UPTIME_PERCENT
        }
    }


def check_scale_limit_proximity(
    current_value: int,
    limit_name: str
) -> dict:
    """
    Check how close current value is to limit.
    
    Args:
        current_value: Current metric value
        limit_name: Name of the limit to check
    
    Returns:
        Dictionary with proximity information
    """
    limits = ScaleLimits()
    
    limit_map = {
        "artifacts": limits.MAX_ARTIFACTS,
        "artifact_size": limits.MAX_ARTIFACT_SIZE,
        "writes_per_second": limits.WRITES_PER_SECOND_LIMIT,
        "reads_per_second": limits.READS_PER_SECOND_LIMIT
    }
    
    limit_value = limit_map.get(limit_name)
    if not limit_value:
        return {"error": f"Unknown limit: {limit_name}"}
    
    percentage = (current_value / limit_value) * 100
    
    if percentage >= 90:
        status = "critical"
        message = "Approaching limit - immediate action required"
    elif percentage >= 80:
        status = "warning"
        message = "Nearing limit - plan capacity increase"
    elif percentage >= 70:
        status = "caution"
        message = "Monitor closely"
    else:
        status = "healthy"
        message = "Within safe limits"
    
    return {
        "limit_name": limit_name,
        "current_value": current_value,
        "limit_value": limit_value,
        "percentage_used": round(percentage, 2),
        "status": status,
        "message": message
    }
