"""
Scan metadata models for persistence
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ScanMetadata(BaseModel):
    """Metadata for a scan stored in the history"""
    scan_id: str
    repository_path: str
    scan_type: str = "full"  # full, quick, ui-only, etc.
    performed_by: str = "system"  # User who performed the scan
    created_at: str  # ISO format timestamp
    completed_at: Optional[str] = None
    status: str = "queued"  # queued, discovering, scanning, completed, error, failed
    viewed: bool = False
    files_scanned: int = 0
    nodes_found: int = 0
    total_files: Optional[int] = None
    scan_duration: float = 0.0
    errors: List[str] = Field(default_factory=list)


class ScanListItem(BaseModel):
    """Scan item in the list view"""
    scan_id: str
    repository_path: str
    repository_name: str
    scan_type: str
    performed_by: str
    created_at: str
    completed_at: Optional[str]
    status: str
    viewed: bool
    files_scanned: int
    nodes_found: int
    scan_duration: float


class ScanListResponse(BaseModel):
    """Response for listing scans"""
    total: int
    scans: List[ScanListItem]


class UnviewedCountResponse(BaseModel):
    """Response for unviewed scan count"""
    count: int
