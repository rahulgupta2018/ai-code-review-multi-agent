"""
Output Manager

Central output coordination and format management.
Manages the generation and coordination of different output formats.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """Supported output formats."""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    XML = "xml"
    MARKDOWN = "markdown"
    CSV = "csv"


@dataclass
class OutputRequest:
    """Request for generating output."""
    agent_name: str
    analysis_results: Dict[str, Any]
    formats: List[OutputFormat]
    output_dir: str
    metadata: Dict[str, Any]


@dataclass
class OutputResult:
    """Result of output generation."""
    success: bool
    generated_files: List[str]
    formats: List[OutputFormat]
    errors: List[str]
    metadata: Dict[str, Any]


class OutputManager:
    """Manages output generation across all agents and formats."""
    
    def __init__(self, base_output_dir: str = "outputs"):
        """Initialize the output manager."""
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        
        # Initialize generators
        self._report_generator = None
        self._dashboard_exporter = None
        self._template_engine = None
        
    def generate_output(self, request: OutputRequest) -> OutputResult:
        """Generate output in requested formats."""
        try:
            # Create agent-specific output directory
            agent_output_dir = self.base_output_dir / request.agent_name
            agent_output_dir.mkdir(exist_ok=True)
            
            generated_files = []
            errors = []
            
            for output_format in request.formats:
                try:
                    file_path = self._generate_format(
                        request.analysis_results,
                        output_format,
                        agent_output_dir,
                        request.metadata
                    )
                    if file_path:
                        generated_files.append(file_path)
                        
                except Exception as e:
                    error_msg = f"Failed to generate {output_format.value} format: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return OutputResult(
                success=len(generated_files) > 0,
                generated_files=generated_files,
                formats=request.formats,
                errors=errors,
                metadata={"agent": request.agent_name, "timestamp": self._get_timestamp()}
            )
            
        except Exception as e:
            logger.error(f"Output generation failed for {request.agent_name}: {e}")
            return OutputResult(
                success=False,
                generated_files=[],
                formats=request.formats,
                errors=[str(e)],
                metadata={}
            )
    
    def _generate_format(self, results: Dict[str, Any], output_format: OutputFormat, 
                        output_dir: Path, metadata: Dict[str, Any]) -> Optional[str]:
        """Generate output in a specific format."""
        
        if output_format == OutputFormat.JSON:
            return self._generate_json(results, output_dir, metadata)
        elif output_format == OutputFormat.HTML:
            return self._generate_html(results, output_dir, metadata)
        elif output_format == OutputFormat.PDF:
            return self._generate_pdf(results, output_dir, metadata)
        elif output_format == OutputFormat.XML:
            return self._generate_xml(results, output_dir, metadata)
        elif output_format == OutputFormat.MARKDOWN:
            return self._generate_markdown(results, output_dir, metadata)
        elif output_format == OutputFormat.CSV:
            return self._generate_csv(results, output_dir, metadata)
        else:
            logger.warning(f"Unsupported output format: {output_format}")
            return None
    
    def _generate_json(self, results: Dict[str, Any], output_dir: Path, 
                      metadata: Dict[str, Any]) -> str:
        """Generate JSON output."""
        import json
        
        output_file = output_dir / "findings" / f"analysis_{self._get_timestamp()}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        output_data = {
            "metadata": metadata,
            "analysis_results": results,
            "generated_at": self._get_timestamp()
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        logger.info(f"Generated JSON output: {output_file}")
        return str(output_file)
    
    def _generate_html(self, results: Dict[str, Any], output_dir: Path, 
                      metadata: Dict[str, Any]) -> str:
        """Generate HTML report."""
        output_file = output_dir / "reports" / f"report_{self._get_timestamp()}.html"
        output_file.parent.mkdir(exist_ok=True)
        
        # TODO: Implement proper HTML template rendering
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Code Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ color: #333; border-bottom: 2px solid #ddd; }}
                .findings {{ margin: 20px 0; }}
                .finding {{ background: #f9f9f9; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Code Analysis Report</h1>
                <p>Generated: {self._get_timestamp()}</p>
            </div>
            <div class="findings">
                <h2>Analysis Results</h2>
                <pre>{str(results)}</pre>
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        logger.info(f"Generated HTML report: {output_file}")
        return str(output_file)
    
    def _generate_pdf(self, results: Dict[str, Any], output_dir: Path, 
                     metadata: Dict[str, Any]) -> str:
        """Generate PDF report."""
        # TODO: Implement PDF generation (e.g., using reportlab)
        output_file = output_dir / "reports" / f"report_{self._get_timestamp()}.pdf"
        output_file.parent.mkdir(exist_ok=True)
        
        # Placeholder: create empty PDF file
        with open(output_file, 'w') as f:
            f.write("PDF generation not yet implemented")
            
        logger.info(f"Generated PDF report (placeholder): {output_file}")
        return str(output_file)
    
    def _generate_xml(self, results: Dict[str, Any], output_dir: Path, 
                     metadata: Dict[str, Any]) -> str:
        """Generate XML output."""
        # TODO: Implement XML generation
        output_file = output_dir / "findings" / f"analysis_{self._get_timestamp()}.xml"
        output_file.parent.mkdir(exist_ok=True)
        
        # Placeholder XML
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <analysis_report generated="{self._get_timestamp()}">
            <metadata>{str(metadata)}</metadata>
            <results>{str(results)}</results>
        </analysis_report>"""
        
        with open(output_file, 'w') as f:
            f.write(xml_content)
            
        logger.info(f"Generated XML output: {output_file}")
        return str(output_file)
    
    def _generate_markdown(self, results: Dict[str, Any], output_dir: Path, 
                          metadata: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        output_file = output_dir / "reports" / f"report_{self._get_timestamp()}.md"
        output_file.parent.mkdir(exist_ok=True)
        
        markdown_content = f"""# Code Analysis Report

Generated: {self._get_timestamp()}

## Metadata
{str(metadata)}

## Analysis Results
```json
{str(results)}
```
"""
        
        with open(output_file, 'w') as f:
            f.write(markdown_content)
            
        logger.info(f"Generated Markdown report: {output_file}")
        return str(output_file)
    
    def _generate_csv(self, results: Dict[str, Any], output_dir: Path, 
                     metadata: Dict[str, Any]) -> str:
        """Generate CSV export."""
        # TODO: Implement proper CSV generation for findings
        output_file = output_dir / "metrics" / f"metrics_{self._get_timestamp()}.csv"
        output_file.parent.mkdir(exist_ok=True)
        
        csv_content = "metric,value,timestamp\n"
        csv_content += f"analysis_completed,1,{self._get_timestamp()}\n"
        
        with open(output_file, 'w') as f:
            f.write(csv_content)
            
        logger.info(f"Generated CSV metrics: {output_file}")
        return str(output_file)
    
    def get_agent_output_dir(self, agent_name: str) -> Path:
        """Get output directory for a specific agent."""
        return self.base_output_dir / agent_name
    
    def list_generated_files(self, agent_name: Optional[str] = None) -> List[str]:
        """List all generated output files."""
        files = []
        search_dir = self.base_output_dir / agent_name if agent_name else self.base_output_dir
        
        if search_dir.exists():
            for file_path in search_dir.rglob("*"):
                if file_path.is_file():
                    files.append(str(file_path))
                    
        return sorted(files)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# Global output manager instance
output_manager = OutputManager()