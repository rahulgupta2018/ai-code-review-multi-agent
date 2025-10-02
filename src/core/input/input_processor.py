"""
Input Processor

Multi-source ingestion engine for code review system.
Supports local directories, git repositories, GitHub/GitLab API, ZIP archives, and single files.
"""
import os
import zipfile
import tempfile
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class InputSource:
    """Represents an input source for code analysis."""
    source_type: str  # local, git, github, gitlab, zip, file
    path: str
    metadata: Dict[str, Any]


@dataclass
class ProcessedFile:
    """Represents a processed file ready for analysis."""
    file_path: str
    content: str
    language: Optional[str]
    size: int
    metadata: Dict[str, Any]


class InputProcessor:
    """Processes various input sources for code analysis."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the input processor."""
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        self.supported_extensions = {
            '.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.cxx', 
            '.cc', '.c', '.h', '.hpp', '.cs', '.swift', '.kt', '.sql'
        }
        
    def process_input(self, input_source: InputSource) -> List[ProcessedFile]:
        """Process an input source and return processed files."""
        try:
            if input_source.source_type == "local":
                return self._process_local_directory(input_source.path)
            elif input_source.source_type == "file":
                return self._process_single_file(input_source.path)
            elif input_source.source_type == "git":
                return self._process_git_repository(input_source.path, input_source.metadata)
            elif input_source.source_type == "github":
                return self._process_github_repository(input_source.path, input_source.metadata)
            elif input_source.source_type == "gitlab":
                return self._process_gitlab_repository(input_source.path, input_source.metadata)
            elif input_source.source_type == "zip":
                return self._process_zip_archive(input_source.path)
            else:
                logger.error(f"Unsupported input source type: {input_source.source_type}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to process input source {input_source.path}: {e}")
            return []
    
    def _process_local_directory(self, directory_path: str) -> List[ProcessedFile]:
        """Process a local directory."""
        processed_files = []
        dir_path = Path(directory_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and self._is_supported_file(file_path):
                processed_file = self._read_file(file_path)
                if processed_file:
                    processed_files.append(processed_file)
                    
        logger.info(f"Processed {len(processed_files)} files from {directory_path}")
        return processed_files
    
    def _process_single_file(self, file_path: str) -> List[ProcessedFile]:
        """Process a single file."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            logger.error(f"File not found: {file_path}")
            return []
            
        if not self._is_supported_file(path):
            logger.warning(f"Unsupported file type: {file_path}")
            return []
            
        processed_file = self._read_file(path)
        return [processed_file] if processed_file else []
    
    def _process_git_repository(self, repo_url: str, metadata: Dict[str, Any]) -> List[ProcessedFile]:
        """Process a git repository."""
        # TODO: Implement git clone and processing
        logger.info(f"Processing git repository: {repo_url}")
        # Placeholder implementation
        return []
    
    def _process_github_repository(self, repo_path: str, metadata: Dict[str, Any]) -> List[ProcessedFile]:
        """Process a GitHub repository via API."""
        # TODO: Implement GitHub API integration
        logger.info(f"Processing GitHub repository: {repo_path}")
        # Placeholder implementation
        return []
    
    def _process_gitlab_repository(self, repo_path: str, metadata: Dict[str, Any]) -> List[ProcessedFile]:
        """Process a GitLab repository via API."""
        # TODO: Implement GitLab API integration
        logger.info(f"Processing GitLab repository: {repo_path}")
        # Placeholder implementation
        return []
    
    def _process_zip_archive(self, zip_path: str) -> List[ProcessedFile]:
        """Process a ZIP archive."""
        processed_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Extract to temporary directory
                extract_dir = self.temp_dir / f"zip_extract_{os.getpid()}"
                zip_file.extractall(extract_dir)
                
                # Process extracted files
                processed_files = self._process_local_directory(str(extract_dir))
                
                # Clean up temporary directory
                self._cleanup_temp_dir(extract_dir)
                
        except Exception as e:
            logger.error(f"Failed to process ZIP archive {zip_path}: {e}")
            
        return processed_files
    
    def _read_file(self, file_path: Path) -> Optional[ProcessedFile]:
        """Read and process a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Detect language from extension
            language = self._detect_language(file_path)
            
            return ProcessedFile(
                file_path=str(file_path),
                content=content,
                language=language,
                size=len(content),
                metadata={
                    "extension": file_path.suffix,
                    "name": file_path.name,
                    "directory": str(file_path.parent)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if a file is supported for analysis."""
        return file_path.suffix.lower() in self.supported_extensions
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        from ..config.language_config import language_config
        return language_config.detect_language_from_extension(file_path.suffix)
    
    def _cleanup_temp_dir(self, temp_dir: Path):
        """Clean up temporary directory."""
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
    
    def get_supported_extensions(self) -> set:
        """Get set of supported file extensions."""
        return self.supported_extensions.copy()
    
    def add_supported_extension(self, extension: str):
        """Add a supported file extension."""
        self.supported_extensions.add(extension.lower())
    
    def filter_files_by_language(self, files: List[ProcessedFile], language: str) -> List[ProcessedFile]:
        """Filter files by programming language."""
        return [f for f in files if f.language and f.language.lower() == language.lower()]