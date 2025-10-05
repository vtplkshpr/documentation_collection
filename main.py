"""
Documentation Collection Plugin for lkwolfSAI Ecosystem
Plug-and-Play Implementation
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add current directory to path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import BasePlugin
sys.path.append(str(Path(__file__).parent.parent))
from base_plugin import BasePlugin, PluginInfo, PluginStatus

# Try to import optional dependencies
try:
    from dotenv import load_dotenv
    load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

try:
    from utils.config import config
    from utils.database import db_manager
    from services.search_service import SearchService
    from services.file_manager import FileManager
    from core.redis_manager import get_redis_manager
    HAS_FULL_DEPS = True
except ImportError as e:
    HAS_FULL_DEPS = False
    print(f"Warning: Some dependencies not available: {e}")

# Setup logging
logger = logging.getLogger(__name__)

class DocumentationCollectionPlugin(BasePlugin):
    """Documentation Collection plugin implementation"""
    
    def __init__(self):
        self._plugin_info = PluginInfo(
            name="documentation_collection",
            version="1.0.0",
            description="Search and collect online documents in multiple languages",
            author="lkwolfSAI Team",
            status=PluginStatus.ACTIVE,
            dependencies=[
                "click>=8.0.0",
                "rich>=13.0.0",
                "python-dotenv>=1.0.0",
                "requests>=2.25.0"
            ],
            supported_languages=["en", "vi", "ja", "ko", "ru", "fa", "zh"],
            required_services=[],
            config_schema={
                "MAX_RESULTS_PER_ENGINE": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum results per search engine"
                },
                "REQUEST_DELAY": {
                    "type": "float",
                    "default": 1.0,
                    "description": "Delay between requests in seconds"
                }
            },
            commands=[
                {
                    "name": "search",
                    "description": "Search and collect documents",
                    "options": [
                        {
                            "name": "query",
                            "type": "string",
                            "required": True,
                            "help": "Search topic/subject"
                        },
                        {
                            "name": "criteria",
                            "type": "string",
                            "required": False,
                            "help": "Filter criteria for AI analysis"
                        },
                        {
                            "name": "max-results",
                            "type": "integer",
                            "required": False,
                            "help": "Max results per engine (default: 10)"
                        }
                    ]
                }
            ]
        )
        self._initialized = False
        self._search_service = None
        self._file_manager = None
    
    @property
    def plugin_info(self) -> PluginInfo:
        """Return plugin metadata"""
        return self._plugin_info
    
    async def initialize(self) -> bool:
        """Initialize plugin"""
        try:
            logger.info(f"Initializing {self.plugin_info.name}...")
            
            # Initialize services if available
            if HAS_FULL_DEPS:
                try:
                    self._search_service = SearchService()
                    self._file_manager = FileManager()
                    logger.info("✓ Full services initialized")
                except Exception as e:
                    logger.warning(f"Some services not available: {e}")
                    self._search_service = None
                    self._file_manager = None
            else:
                logger.info("✓ Running in minimal mode")
            
            self._initialized = True
            logger.info(f"✓ {self.plugin_info.name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.plugin_info.name}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        try:
            # Cleanup services
            self._search_service = None
            self._file_manager = None
            self._initialized = False
            logger.info(f"✓ {self.plugin_info.name} cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup {self.plugin_info.name}: {e}")
            return False
    
    def get_cli_commands(self) -> list:
        """Return Click commands for CLI integration"""
        return [main]
    
    async def health_check(self) -> Dict[str, Any]:
        """Return plugin health status"""
        return {
            "plugin": self.plugin_info.name,
            "version": self.plugin_info.version,
            "status": "healthy" if self._initialized else "not_initialized",
            "services": {
                "search_service": "healthy" if self._search_service else "not_available",
                "file_manager": "healthy" if self._file_manager else "not_available",
                "dependencies": "full" if HAS_FULL_DEPS else "minimal"
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> list:
        """Validate plugin configuration"""
        errors = []
        
        # Validate numeric settings
        if "MAX_RESULTS_PER_ENGINE" in config:
            try:
                value = float(config["MAX_RESULTS_PER_ENGINE"])
                if value < 1:
                    errors.append("MAX_RESULTS_PER_ENGINE must be positive")
            except (ValueError, TypeError):
                errors.append("MAX_RESULTS_PER_ENGINE must be a valid number")
        
        if "REQUEST_DELAY" in config:
            try:
                value = float(config["REQUEST_DELAY"])
                if value < 0:
                    errors.append("REQUEST_DELAY must be non-negative")
            except (ValueError, TypeError):
                errors.append("REQUEST_DELAY must be a valid number")
        
        return errors
    
    async def run(self, data: Any = None) -> Any:
        """Main plugin execution method"""
        if not self._initialized:
            await self.initialize()
        
        return {
            "status": "success",
            "message": f"{self.plugin_info.name} executed",
            "data": data
        }

# CLI Implementation
console = Console()

class DocumentationCollectionCLI:
    """CLI interface for documentation collection"""
    
    def __init__(self):
        self.plugin = DocumentationCollectionPlugin()
    
    async def run_search(self, query: str, criteria: str = None, max_results: int = 10, 
                        export_format: str = "csv", languages: str = None, 
                        session_id: str = None, stats: bool = False, 
                        interactive: bool = False, ai_analysis: bool = True,
                        no_ai: bool = False, enable_ai_optimization: bool = False,
                        search_pages: int = 1, aggressive_search: bool = False):
        """Run documentation collection search"""
        
        if not await self.plugin.initialize():
            console.print("[red]Failed to initialize plugin[/red]")
            return
        
        try:
            if stats:
                await self._show_stats()
                return
            
            if session_id:
                await self._show_session_results(session_id, export_format)
                return
            
            if interactive:
                await self._interactive_mode()
                return
            
            # Run search
            await self._run_search(query, criteria, max_results, export_format, 
                                 languages, ai_analysis, no_ai, enable_ai_optimization,
                                 search_pages, aggressive_search)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            await self.plugin.cleanup()
    
    async def _run_search(self, query: str, criteria: str, max_results: int,
                         export_format: str, languages: str, ai_analysis: bool,
                         no_ai: bool, enable_ai_optimization: bool,
                         search_pages: int, aggressive_search: bool):
        """Execute the search"""
        console.print(f"\n[bold blue]🔍 Starting documentation collection...[/bold blue]")
        console.print(f"Query: [cyan]{query}[/cyan]")
        
        if not self.plugin._search_service:
            console.print("[red]Search service not available. Running in minimal mode.[/red]")
            console.print("[yellow]Please install full dependencies for complete functionality.[/yellow]")
            return
        
        # Parse languages
        lang_list = []
        if languages:
            lang_list = [lang.strip() for lang in languages.split(',')]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching...", total=None)
            
            # Prepare search criteria
            search_criteria = {
                "criteria": criteria,
                "max_results_per_engine": max_results,
                "additional_languages": lang_list,
                "ai_analysis": ai_analysis,
                "ai_optimization": enable_ai_optimization,
                "search_pages": search_pages,
                "aggressive_search": aggressive_search
            } if criteria or lang_list or aggressive_search else None
            
            # Run search
            session_id = await self.plugin._search_service.search_documents(
                query=query,
                search_criteria=search_criteria
            )
            
            progress.update(task, description="Search completed!")
        
        if session_id:
            console.print(f"\n[green]✓ Search completed! Session ID: {session_id}[/green]")
            
            # Export results
            if export_format in ["csv", "excel", "both"]:
                await self._export_results(session_id, export_format)
        else:
            console.print("\n[red]✗ Search failed! No session created.[/red]")
    
    async def _export_results(self, session_id: str, export_format: str):
        """Export search results"""
        console.print(f"\n[blue]📊 Exporting results...[/blue]")
        
        if not self.plugin._file_manager:
            console.print("[red]File manager not available. Cannot export results.[/red]")
            return
        
        if export_format in ["csv", "both"]:
            csv_file = self.plugin._file_manager.export_session_to_csv(int(session_id))
            if csv_file:
                console.print(f"[green]✓ CSV exported: {csv_file}[/green]")
        
        if export_format in ["excel", "both"]:
            excel_file = self.plugin._file_manager.export_session_to_excel(int(session_id))
            if excel_file:
                console.print(f"[green]✓ Excel exported: {excel_file}[/green]")
    
    async def _show_stats(self):
        """Show storage statistics"""
        console.print("\n[bold blue]📊 Storage Statistics[/bold blue]")
        
        if not self.plugin._file_manager:
            console.print("[red]File manager not available. Cannot show statistics.[/red]")
            return
        
        stats = self.plugin._file_manager.get_storage_stats()
        
        if stats:
            table = Table(title="Storage Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in stats.items():
                table.add_row(key, str(value))
            
            console.print(table)
        else:
            console.print("[yellow]No statistics available[/yellow]")
    
    async def _show_session_results(self, session_id: str, export_format: str):
        """Show results for a specific session"""
        console.print(f"\n[bold blue]📋 Session Results: {session_id}[/bold blue]")
        console.print("[yellow]Session results display not implemented yet[/yellow]")
    
    async def _interactive_mode(self):
        """Interactive mode"""
        console.print("\n[bold blue]🎯 Interactive Mode[/bold blue]")
        console.print("[yellow]Interactive mode not implemented yet[/yellow]")

# CLI Commands
@click.command()
@click.option('--query', '-q', help='Search topic/subject')
@click.option('--criteria', '-c', help='Filter criteria for AI analysis')
@click.option('--max-results', '-m', default=10, help='Max results per engine')
@click.option('--export-format', '-f', default='csv', type=click.Choice(['csv', 'excel', 'both']), help='Export format')
@click.option('--languages', '-l', help='Additional languages (comma-separated)')
@click.option('--session-id', '-s', help='Session ID to view results')
@click.option('--stats', is_flag=True, help='Show storage statistics')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--ai-analysis', '-a', is_flag=True, default=True, help='Enable AI content analysis')
@click.option('--no-ai', is_flag=True, help='Disable AI content analysis')
@click.option('--enable-ai-optimization', is_flag=True, help='Enable AI query optimization')
@click.option('--search-pages', '-p', default=1, help='Number of search pages to fetch')
@click.option('--aggressive-search', is_flag=True, help='Use aggressive search settings')
def main(query, criteria, max_results, export_format, languages, session_id, 
         stats, interactive, ai_analysis, no_ai, enable_ai_optimization,
         search_pages, aggressive_search):
    """Documentation Collection Plugin - Search and collect online documents"""
    
    if not any([query, session_id, stats, interactive]):
        console.print("[red]Error: Please provide a query or use --stats, --session-id, or --interactive[/red]")
        console.print("Use --help for more information")
        return
    
    cli = DocumentationCollectionCLI()
    asyncio.run(cli.run_search(
        query=query or "",
        criteria=criteria,
        max_results=max_results,
        export_format=export_format,
        languages=languages,
        session_id=session_id,
        stats=stats,
        interactive=interactive,
        ai_analysis=ai_analysis,
        no_ai=no_ai,
        enable_ai_optimization=enable_ai_optimization,
        search_pages=search_pages,
        aggressive_search=aggressive_search
    ))

if __name__ == "__main__":
    main()