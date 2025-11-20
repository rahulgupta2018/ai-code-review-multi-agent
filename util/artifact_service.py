"""
File-based artifact storage for code review system.

This service implements the artifact storage layer as documented in
MULTI_AGENT_STATE_MANAGEMENT_DESIGN.md.

Artifacts are stored in a structured directory hierarchy:
./artifacts/{app_name}/{user_id}/
    ├── inputs/                 # User-submitted code
    ├── reports/                # Final consolidated reports
    └── sub_agent_outputs/      # Individual agent analysis results
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.adk.artifacts import BaseArtifactService
from google.adk.artifacts.base_artifact_service import ArtifactVersion
from google.genai import types

logger = logging.getLogger(__name__)


class FileArtifactService(BaseArtifactService):
    """
    File-based artifact storage service.
    
    Stores artifacts on disk with metadata for:
    - Input code files
    - Final reports
    - Sub-agent analysis outputs
    
    Each artifact is saved with:
    - Main content file (e.g., code_input_123.py)
    - Metadata file (e.g., code_input_123.py.meta.json)
    """
    
    def __init__(self, base_dir: str = "./artifacts"):
        """
        Initialize artifact service.
        
        Args:
            base_dir: Base directory for all artifacts (default: ./artifacts)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileArtifactService] Initialized with base_dir: {self.base_dir}")
    
    def _get_artifact_dir(self, app_name: str, user_id: str) -> Path:
        """Get or create artifact directory for app/user."""
        artifact_dir = self.base_dir / app_name / user_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir
    
    def _determine_subdir(self, filename: str) -> str:
        """Determine subdirectory based on filename pattern."""
        if filename.startswith("code_input_") or filename.startswith("input_"):
            return "inputs"
        elif filename.startswith("report_"):
            return "reports"
        elif filename.startswith("analysis_"):
            return "sub_agent_outputs"
        else:
            return "other"
    
    async def save_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        artifact: types.Part,
        session_id: Optional[str] = None,
        custom_metadata: Optional[dict] = None
    ) -> int:
        """
        Save artifact to disk with metadata.
        
        Args:
            app_name: Application name (e.g., "Code_Review_System")
            user_id: User identifier
            filename: Artifact filename (determines subdirectory)
            artifact: Content to save (types.Part with text or data)
            session_id: Optional session ID for tracking
            custom_metadata: Optional additional metadata
            
        Returns:
            Version number (always 1 for now - versioning in Phase 2)
        """
        try:
            # Get artifact directory
            artifact_dir = self._get_artifact_dir(app_name, user_id)
            
            # Determine subdirectory
            subdir_name = self._determine_subdir(filename)
            subdir = artifact_dir / subdir_name
            subdir.mkdir(exist_ok=True)
            
            # Full file path
            file_path = subdir / filename
            
            # Save artifact content
            if hasattr(artifact, 'text') and artifact.text:
                file_path.write_text(artifact.text, encoding='utf-8')
                content_type = "text"
                size_bytes = len(artifact.text.encode('utf-8'))
            elif hasattr(artifact, 'inline_data') and artifact.inline_data and artifact.inline_data.data:
                data_bytes = artifact.inline_data.data
                file_path.write_bytes(data_bytes)
                content_type = "binary"
                size_bytes = len(data_bytes)
            else:
                logger.error(f"[FileArtifactService] Artifact has no text or inline_data: {filename}")
                return 0
            
            # Create metadata
            metadata = {
                "filename": filename,
                "app_name": app_name,
                "user_id": user_id,
                "session_id": session_id,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "created_at": datetime.now().isoformat(),
                "version": 1,
                "custom": custom_metadata or {}
            }
            
            # Save metadata
            metadata_path = file_path.with_suffix(file_path.suffix + ".meta.json")
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            
            logger.info(
                f"[FileArtifactService] Saved artifact: {subdir_name}/{filename} "
                f"({size_bytes} bytes)"
            )
            
            return 1  # Version number
            
        except Exception as e:
            logger.error(f"[FileArtifactService] Error saving artifact {filename}: {e}")
            raise
    
    async def load_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None
    ) -> Optional[types.Part]:
        """
        Load artifact from disk.
        
        Args:
            app_name: Application name
            user_id: User identifier
            filename: Artifact filename
            session_id: Optional session ID (not used in Phase 1)
            version: Optional version number (not used in Phase 1)
            
        Returns:
            types.Part with artifact content, or None if not found
        """
        try:
            artifact_dir = self._get_artifact_dir(app_name, user_id)
            
            # Search in all subdirectories
            for subdir_name in ["inputs", "reports", "sub_agent_outputs", "other"]:
                subdir = artifact_dir / subdir_name
                if not subdir.exists():
                    continue
                
                file_path = subdir / filename
                if file_path.exists():
                    # Load metadata to determine content type
                    metadata_path = file_path.with_suffix(file_path.suffix + ".meta.json")
                    content_type = "text"  # Default
                    
                    if metadata_path.exists():
                        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
                        content_type = metadata.get("content_type", "text")
                    
                    # Load content
                    if content_type == "text":
                        content = file_path.read_text(encoding='utf-8')
                        logger.info(f"[FileArtifactService] Loaded artifact: {subdir_name}/{filename}")
                        return types.Part(text=content)
                    else:
                        data_bytes = file_path.read_bytes()
                        logger.info(f"[FileArtifactService] Loaded artifact: {subdir_name}/{filename}")
                        # For binary data, use inline_data
                        return types.Part(inline_data=types.Blob(data=data_bytes, mime_type="application/octet-stream"))
            
            logger.warning(f"[FileArtifactService] Artifact not found: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"[FileArtifactService] Error loading artifact {filename}: {e}")
            raise
    
    async def list_artifact_keys(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: Optional[str] = None
    ) -> list[str]:
        """
        List all artifact filenames for user.
        
        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Optional session ID filter (not used in Phase 1)
            
        Returns:
            List of artifact filenames (relative paths from user directory)
        """
        try:
            artifact_dir = self._get_artifact_dir(app_name, user_id)
            
            if not artifact_dir.exists():
                return []
            
            files = []
            for subdir_name in ["inputs", "reports", "sub_agent_outputs", "other"]:
                subdir = artifact_dir / subdir_name
                if not subdir.exists():
                    continue
                
                # Find all files (excluding .meta.json)
                for file_path in subdir.rglob("*"):
                    if file_path.is_file() and not file_path.name.endswith(".meta.json"):
                        # Store relative path from user directory
                        rel_path = file_path.relative_to(artifact_dir)
                        files.append(str(rel_path))
            
            logger.info(f"[FileArtifactService] Listed {len(files)} artifacts for user {user_id}")
            return files
            
        except Exception as e:
            logger.error(f"[FileArtifactService] Error listing artifacts: {e}")
            raise
    
    def get_artifact_path(self, app_name: str, user_id: str, filename: str) -> Optional[Path]:
        """
        Get full file path for artifact (helper method for direct file access).
        
        Args:
            app_name: Application name
            user_id: User identifier
            filename: Artifact filename
            
        Returns:
            Path object if artifact exists, None otherwise
        """
        artifact_dir = self._get_artifact_dir(app_name, user_id)
        
        for subdir_name in ["inputs", "reports", "sub_agent_outputs", "other"]:
            subdir = artifact_dir / subdir_name
            if not subdir.exists():
                continue
            
            file_path = subdir / filename
            if file_path.exists():
                return file_path
        
        return None
    
    def get_artifact_metadata(
        self, app_name: str, user_id: str, filename: str
    ) -> Optional[dict]:
        """
        Get metadata for artifact without loading full content.
        
        Args:
            app_name: Application name
            user_id: User identifier
            filename: Artifact filename
            
        Returns:
            Metadata dict if found, None otherwise
        """
        artifact_path = self.get_artifact_path(app_name, user_id, filename)
        if not artifact_path:
            return None
        
        metadata_path = artifact_path.with_suffix(artifact_path.suffix + ".meta.json")
        if not metadata_path.exists():
            return None
        
        try:
            return json.loads(metadata_path.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(f"[FileArtifactService] Error loading metadata for {filename}: {e}")
            return None
    
    # Implement remaining abstract methods from BaseArtifactService
    
    async def delete_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None,
        version: Optional[int] = None
    ) -> None:
        """Delete artifact from storage (not implemented in Phase 1)."""
        logger.warning("[FileArtifactService] delete_artifact not implemented in Phase 1")
    
    async def list_versions(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None
    ) -> list[int]:
        """List artifact versions (not implemented in Phase 1 - always returns [1])."""
        artifact_path = self.get_artifact_path(app_name, user_id, filename)
        if artifact_path and artifact_path.exists():
            return [1]
        return []
    
    async def delete_version(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        version: int,
        session_id: Optional[str] = None
    ) -> None:
        """Delete specific artifact version (not implemented in Phase 1)."""
        logger.warning("[FileArtifactService] delete_version not implemented in Phase 1")
    
    async def replace_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        artifact: types.Part,
        session_id: Optional[str] = None,
        custom_metadata: Optional[dict] = None
    ) -> int:
        """
        Replace existing artifact (same as save_artifact in Phase 1 - always overwrites).
        
        Args:
            Same as save_artifact
            
        Returns:
            Version number (always 1)
        """
        return await self.save_artifact(
            app_name=app_name,
            user_id=user_id,
            filename=filename,
            artifact=artifact,
            session_id=session_id,
            custom_metadata=custom_metadata
        )
    
    async def list_artifact_versions(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: Optional[str] = None
    ) -> list[ArtifactVersion]:
        """List artifact versions (Phase 1: returns single version if exists)."""
        artifact_path = self.get_artifact_path(app_name, user_id, filename)
        if not artifact_path or not artifact_path.exists():
            return []
        
        # Get metadata
        metadata = self.get_artifact_metadata(app_name, user_id, filename) or {}
        
        # Create ArtifactVersion object
        version_info = ArtifactVersion(
            version=1,
            canonical_uri=f"artifact://{filename}",
            custom_metadata=metadata.get("custom", {}),
            create_time=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())).timestamp(),
            mime_type=metadata.get("mime_type", "text/plain")
        )
        
        return [version_info]
    
    async def get_artifact_version(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Optional[ArtifactVersion]:
        """Get specific version of artifact (Phase 1: ignores version, returns version 1 if exists)."""
        versions = await self.list_artifact_versions(
            app_name=app_name,
            user_id=user_id,
            filename=filename,
            session_id=session_id
        )
        
        if versions:
            return versions[0]  # Always return first (only) version in Phase 1
        return None
