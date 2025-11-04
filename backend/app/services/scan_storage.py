"""
Scan storage service for persisting scan history
"""
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.models.scan import ScanMetadata, ScanListItem


class ScanStorage:
    """Service for managing scan persistence"""

    def __init__(self, storage_dir: str = "/tmp/scans"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / "scan_metadata.json"
        self._initialize_metadata_file()

    def _initialize_metadata_file(self):
        """Initialize metadata file if it doesn't exist"""
        if not self.metadata_file.exists():
            with open(self.metadata_file, 'w') as f:
                json.dump([], f)

    def _load_all_metadata(self) -> List[dict]:
        """Load all scan metadata"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return []

    def _save_all_metadata(self, metadata_list: List[dict]):
        """Save all scan metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_list, f, indent=2)

    def create_scan(self, scan_metadata: ScanMetadata) -> ScanMetadata:
        """Create a new scan entry"""
        metadata_list = self._load_all_metadata()

        # Add new scan
        metadata_list.append(scan_metadata.model_dump())
        self._save_all_metadata(metadata_list)

        return scan_metadata

    def update_scan(self, scan_id: str, updates: dict) -> Optional[ScanMetadata]:
        """Update scan metadata"""
        metadata_list = self._load_all_metadata()

        for i, scan in enumerate(metadata_list):
            if scan['scan_id'] == scan_id:
                metadata_list[i].update(updates)
                self._save_all_metadata(metadata_list)
                return ScanMetadata(**metadata_list[i])

        return None

    def get_scan(self, scan_id: str) -> Optional[ScanMetadata]:
        """Get scan metadata by ID"""
        metadata_list = self._load_all_metadata()

        for scan in metadata_list:
            if scan['scan_id'] == scan_id:
                return ScanMetadata(**scan)

        return None

    def list_scans(self, limit: Optional[int] = None, offset: int = 0) -> List[ScanListItem]:
        """List all scans with pagination"""
        metadata_list = self._load_all_metadata()

        # Sort by created_at descending (most recent first)
        sorted_scans = sorted(
            metadata_list,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )

        # Apply pagination
        if limit:
            sorted_scans = sorted_scans[offset:offset + limit]
        else:
            sorted_scans = sorted_scans[offset:]

        # Convert to ScanListItem
        result = []
        for scan in sorted_scans:
            repo_path = scan.get('repository_path', '')
            repo_name = Path(repo_path).name if repo_path else 'Unknown'

            result.append(ScanListItem(
                scan_id=scan['scan_id'],
                repository_path=scan.get('repository_path', ''),
                repository_name=repo_name,
                scan_type=scan.get('scan_type', 'full'),
                performed_by=scan.get('performed_by', 'system'),
                created_at=scan.get('created_at', ''),
                completed_at=scan.get('completed_at'),
                status=scan.get('status', 'unknown'),
                viewed=scan.get('viewed', False),
                files_scanned=scan.get('files_scanned', 0),
                nodes_found=scan.get('nodes_found', 0),
                scan_duration=scan.get('scan_duration', 0.0),
            ))

        return result

    def count_total_scans(self) -> int:
        """Get total count of scans"""
        metadata_list = self._load_all_metadata()
        return len(metadata_list)

    def count_unviewed_scans(self) -> int:
        """Get count of unviewed scans"""
        metadata_list = self._load_all_metadata()
        return sum(1 for scan in metadata_list if not scan.get('viewed', False))

    def mark_as_viewed(self, scan_id: str) -> bool:
        """Mark a scan as viewed"""
        result = self.update_scan(scan_id, {'viewed': True})
        return result is not None
