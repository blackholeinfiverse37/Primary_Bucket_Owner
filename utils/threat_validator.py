"""
Threat Validation Utilities
Implements threat detection from doc 14 - BUCKET_THREAT_MODEL.md
"""

from enum import Enum
from typing import Dict, Any, List

class ThreatLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class BucketThreatModel:
    """
    Enterprise threat model for BHIV Bucket.
    Based on doc 14 - BUCKET_THREAT_MODEL.md
    """
    
    THREATS = {
        "T1_ACCESS_BYPASS": {
            "name": "Access Control Bypass",
            "level": ThreatLevel.CRITICAL,
            "description": "Direct database access or credential leakage",
            "mitigations": [
                "API-only access pattern",
                "No MongoDB credentials in code",
                "Integration token validation",
                "Rate limiting per integration"
            ],
            "detection_patterns": [
                "db_connection_string",
                "direct_mongo_access",
                "credential_in_request",
                "db_connection",
                "mongodb://",
                "direct_database"
            ]
        },
        
        "T2_SCHEMA_CORRUPTION": {
            "name": "Schema Corruption",
            "level": ThreatLevel.CRITICAL,
            "description": "Unauthorized schema modification or field injection",
            "mitigations": [
                "Schema validation middleware",
                "Immutable schema enforcement",
                "Schema versioning",
                "Change approval workflow"
            ],
            "detection_patterns": [
                "$schema",
                "$schema_change",
                "collection_mutation",
                "index_modification",
                "field_injection",
                "_id",
                "created_at",
                "updated_at"
            ]
        },
        
        "T3_DATA_LOSS": {
            "name": "Data Loss",
            "level": ThreatLevel.CRITICAL,
            "description": "Accidental or intentional data deletion",
            "mitigations": [
                "Soft-delete with 90-day recovery",
                "Immutable audit trail",
                "Backup procedures",
                "Tombstone markers"
            ],
            "detection_patterns": [
                "bulk_delete",
                "cascade_delete",
                "unvalidated_delete",
                "force_delete",
                "permanent_delete"
            ]
        },
        
        "T4_GOVERNANCE_CIRCUMVENTION": {
            "name": "Governance Circumvention",
            "level": ThreatLevel.HIGH,
            "description": "Attempts to bypass governance gate",
            "mitigations": [
                "Gate validation on every operation",
                "No exceptions for speed",
                "Audit trail of all gate decisions",
                "Escalation protocol (doc 09)"
            ],
            "detection_patterns": [
                "undocumented_integration",
                "unauthorized_product",
                "gate_bypass_attempt",
                "_internal",
                "bypass_validation"
            ]
        },
        
        "T5_SCALE_FAILURE": {
            "name": "Scale Failure",
            "level": ThreatLevel.HIGH,
            "description": "System degradation under load",
            "mitigations": [
                "Load testing at scale",
                "Throughput limits enforced",
                "Connection pool management",
                "Monitoring and alerting"
            ],
            "detection_patterns": [
                "high_query_frequency",
                "batch_operation_overflow",
                "concurrent_writes",
                "excessive_size",
                "rate_limit_exceeded"
            ]
        },
        
        "T6_LEGAL_AMBIGUITY": {
            "name": "Legal Ambiguity",
            "level": ThreatLevel.MEDIUM,
            "description": "Unclear artifact ownership or data provenance",
            "mitigations": [
                "Mandatory ownership fields",
                "Complete audit trail",
                "Clear retention policies",
                "Legal defensibility framework"
            ],
            "detection_patterns": [
                "missing_owner",
                "missing_provenance",
                "unclear_retention",
                "no_audit_trail"
            ]
        },
        
        "T7_OVER_TRUST": {
            "name": "Over-Trust in Provenance",
            "level": ThreatLevel.MEDIUM,
            "description": "Assuming guarantees that don't exist",
            "mitigations": [
                "Honest gaps documented",
                "Explicit guarantees only",
                "No silent assumptions",
                "Phase 2 roadmap for improvements"
            ],
            "detection_patterns": [
                "assumed_immutability",
                "assumed_completeness",
                "undocumented_guarantee"
            ]
        }
    }
    
    @staticmethod
    def get_threat(threat_id: str) -> Dict[str, Any]:
        """Get threat definition by ID"""
        threat = BucketThreatModel.THREATS.get(threat_id)
        if threat:
            return {
                "threat_id": threat_id,
                "name": threat["name"],
                "level": threat["level"].value,
                "description": threat["description"],
                "mitigations": threat["mitigations"],
                "detection_patterns": threat["detection_patterns"]
            }
        return None
    
    @staticmethod
    def get_all_threats() -> Dict[str, Dict[str, Any]]:
        """Get all threats in threat model"""
        result = {}
        for threat_id, threat_data in BucketThreatModel.THREATS.items():
            result[threat_id] = {
                "name": threat_data["name"],
                "level": threat_data["level"].value,
                "description": threat_data["description"],
                "mitigations": threat_data["mitigations"],
                "detection_patterns": threat_data["detection_patterns"]
            }
        return result
    
    @staticmethod
    def detect_threat_pattern(pattern: str) -> List[str]:
        """Find threats matching a detection pattern"""
        matching_threats = []
        
        for threat_id, threat_data in BucketThreatModel.THREATS.items():
            if pattern in threat_data.get("detection_patterns", []):
                matching_threats.append(threat_id)
        
        return matching_threats
    
    @staticmethod
    def scan_for_threats(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan data for threat patterns.
        Returns list of detected threats.
        """
        detected_threats = []
        
        # Convert data to string for pattern matching
        data_str = str(data).lower()
        
        for threat_id, threat_data in BucketThreatModel.THREATS.items():
            for pattern in threat_data.get("detection_patterns", []):
                if pattern.lower() in data_str:
                    detected_threats.append({
                        "threat_id": threat_id,
                        "name": threat_data["name"],
                        "level": threat_data["level"].value,
                        "pattern_matched": pattern,
                        "description": threat_data["description"]
                    })
                    break  # Only report each threat once
        
        return detected_threats
    
    @staticmethod
    def get_threat_level_priority(level: str) -> int:
        """Get numeric priority for threat level (higher = more severe)"""
        priorities = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1
        }
        return priorities.get(level.lower(), 0)
    
    @staticmethod
    def has_critical_threats(threats: List[Dict[str, Any]]) -> bool:
        """Check if any threats are CRITICAL level"""
        return any(
            threat.get("level", "").lower() == "critical" 
            for threat in threats
        )
    
    @staticmethod
    def get_mitigation_recommendations(threat_id: str) -> List[str]:
        """Get mitigation recommendations for a specific threat"""
        threat = BucketThreatModel.THREATS.get(threat_id)
        if threat:
            return threat.get("mitigations", [])
        return []
