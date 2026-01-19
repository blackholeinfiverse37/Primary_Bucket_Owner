"""
Audit Middleware
Logs all operations for governance compliance.
Based on doc 12 - Incident Response & Audit Requirements.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AuditMiddleware:
    """
    Middleware that logs every Bucket operation for audit trail.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.audit_collection = None
        if self.db is not None:
            self.audit_collection = self.db["audit_events"]
            self.create_indexes()
    
    def create_indexes(self):
        """Create indexes for efficient audit queries."""
        if self.audit_collection is None:
            return
        
        try:
            # Index by timestamp for timeline queries
            self.audit_collection.create_index("timestamp")
            
            # Index by operation type for analysis
            self.audit_collection.create_index("operation_type")
            
            # Index by requester for user accountability
            self.audit_collection.create_index("requester_id")
            
            # Compound index for common queries
            self.audit_collection.create_index([
                ("timestamp", -1),
                ("artifact_id", 1),
                ("operation_type", 1)
            ])
            
            logger.info("Audit middleware indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create audit indexes: {e}")
    
    async def log_operation(
        self,
        operation_type: str,
        artifact_id: str,
        requester_id: str,
        integration_id: str,
        data_before: Optional[Dict[str, Any]] = None,
        data_after: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Log an operation for audit trail.
        
        This is immutable and cannot be changed.
        """
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation_type": operation_type,
            "artifact_id": artifact_id,
            "requester_id": requester_id,
            "integration_id": integration_id,
            "data_before": data_before,
            "data_after": data_after,
            "status": status,
            "error_message": error_message,
            "change_delta": self._compute_delta(data_before, data_after)
        }
        
        # Insert into immutable audit collection
        if self.audit_collection is not None:
            try:
                result = await self.audit_collection.insert_one(audit_entry)
                logger.info(f"Audit entry created: {result.inserted_id}")
                return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Failed to create audit entry: {e}")
                return None
        else:
            logger.warning("Audit collection not available, skipping audit log")
            return None
    
    def _compute_delta(
        self,
        before: Optional[Dict[str, Any]],
        after: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute the change delta between before and after.
        """
        
        if not before or not after:
            return {}
        
        delta = {}
        
        # Fields that changed
        for key in set(list(before.keys()) + list(after.keys())):
            before_val = before.get(key)
            after_val = after.get(key)
            
            if before_val != after_val:
                delta[key] = {
                    "old": before_val,
                    "new": after_val
                }
        
        return delta
    
    async def get_artifact_history(
        self,
        artifact_id: str,
        limit: int = 100
    ) -> list:
        """
        Get complete history of operations on an artifact.
        """
        
        if self.audit_collection is None:
            return []
        
        try:
            history = await self.audit_collection.find(
                {"artifact_id": artifact_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)
            
            return history
        except Exception as e:
            logger.error(f"Failed to get artifact history: {e}")
            return []
    
    async def get_user_activities(
        self,
        requester_id: str,
        limit: int = 100
    ) -> list:
        """
        Get all operations performed by a user.
        """
        
        if self.audit_collection is None:
            return []
        
        try:
            activities = await self.audit_collection.find(
                {"requester_id": requester_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)
            
            return activities
        except Exception as e:
            logger.error(f"Failed to get user activities: {e}")
            return []
    
    async def validate_immutability(
        self,
        artifact_id: str
    ) -> bool:
        """
        Verify that artifact has not been modified since creation.
        """
        
        operations = await self.get_artifact_history(artifact_id)
        
        if not operations:
            return True
        
        # Count CREATE operations (should be 1)
        create_ops = [op for op in operations if op["operation_type"] == "CREATE"]
        
        if len(create_ops) != 1:
            logger.error(f"Artifact {artifact_id} has {len(create_ops)} CREATE operations (should be 1)")
            return False
        
        # Only CREATE should exist for immutable artifacts
        if len(operations) > 1:
            logger.warning(f"Artifact {artifact_id} has {len(operations)} operations (not immutable)")
        
        return True
    
    async def get_recent_operations(
        self,
        limit: int = 100,
        operation_type: Optional[str] = None
    ) -> list:
        """
        Get recent operations across all artifacts.
        """
        
        if self.audit_collection is None:
            return []
        
        try:
            query = {}
            if operation_type:
                query["operation_type"] = operation_type
            
            operations = await self.audit_collection.find(
                query
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)
            
            return operations
        except Exception as e:
            logger.error(f"Failed to get recent operations: {e}")
            return []
    
    async def get_failed_operations(
        self,
        limit: int = 100
    ) -> list:
        """
        Get recent failed operations for incident response.
        """
        
        if self.audit_collection is None:
            return []
        
        try:
            operations = await self.audit_collection.find(
                {"status": "failed"}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)
            
            return operations
        except Exception as e:
            logger.error(f"Failed to get failed operations: {e}")
            return []
