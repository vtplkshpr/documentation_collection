"""
Main entry point for documentation collection module
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

# Add current directory to path for imports if not already present
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.config import config
from utils.database import db_manager
from services.search_service import SearchService
from services.file_manager import FileManager
from core.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
console = Console()

class DocumentationCollectionCLI:
    """CLI interface for documentation collection"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.file_manager = FileManager()
    
    def display_banner(self):
        """Display welcome banner"""
        banner = Text("""
╔══════════════════════════════════════════════════════════════╗
║                    DOCUMENTATION COLLECTION                 ║
║                                                              ║
║  Tìm kiếm và thu thập tài liệu online đa ngôn ngữ           ║
║  Multi-language online document search and collection       ║
╚══════════════════════════════════════════════════════════════╝
        """, style="bold blue")
        console.print(Panel(banner, title="Welcome", border_style="blue"))
    
    def display_supported_languages(self):
        """Display supported languages"""
        table = Table(title="Supported Languages")
        table.add_column("Code", style="cyan")
        table.add_column("Language", style="magenta")
        
        for code, name in config.LANGUAGE_NAMES.items():
            table.add_row(code, name)
        
        console.print(table)
    
    def display_search_engines(self):
        """Display available search engines"""
        table = Table(title="Available Search Engines")
        table.add_column("Engine", style="cyan")
        table.add_column("Status", style="green")
        
        for engine in config.ENABLED_SEARCH_ENGINES:
            table.add_row(engine, "✓ Enabled")
        
        console.print(table)
    
    async def search_documents_interactive(self):
        """Interactive document search"""
        console.print("\n[bold green]Starting Document Search[/bold green]")
        
        # Get search topic
        query = click.prompt("Enter your search topic/subject", type=str)
        if not query.strip():
            console.print("[red]Error: Search topic cannot be empty[/red]")
            return None
        
        # Get filter criteria
        criteria = click.prompt("Enter filter criteria for AI analysis (optional)", default="", type=str)
        
        # Get search criteria
        console.print("\n[bold]Search Criteria (optional):[/bold]")
        max_results = click.prompt("Max results per engine", default=config.MAX_RESULTS_PER_ENGINE, type=int)
        
        # Ask about AI analysis (default enabled)
        ai_analysis = True
        if criteria.strip():
            ai_analysis = click.confirm("Enable AI content analysis?", default=True)
        else:
            ai_analysis = click.confirm("Enable AI content analysis?", default=True)
        
        search_criteria = {
            'max_results_per_engine': max_results,
            'user_input': True,
            'filter_criteria': criteria if criteria.strip() else None,
            'ai_analysis': ai_analysis
        }
        
        # Confirm search
        console.print(f"\n[bold]Search Configuration:[/bold]")
        console.print(f"Topic: {query}")
        if criteria.strip():
            console.print(f"Filter criteria: {criteria}")
        console.print(f"Languages: {', '.join(config.SUPPORTED_LANGUAGES)}")
        console.print(f"Engines: {', '.join(config.ENABLED_SEARCH_ENGINES)}")
        console.print(f"Max results per engine: {max_results}")
        console.print(f"AI Analysis: {'Yes' if ai_analysis else 'No'}")
        
        if not click.confirm("\nProceed with search?"):
            console.print("[yellow]Search cancelled[/yellow]")
            return None
        
        # Perform search with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching documents...", total=None)
            
            try:
                session_id = await self.search_service.search_documents(query, search_criteria)
                
                if session_id:
                    progress.update(task, description="Search completed!")
                    console.print(f"\n[green]✓ Search completed successfully![/green]")
                    console.print(f"[bold]Session ID: {session_id}[/bold]")
                    return session_id
                else:
                    progress.update(task, description="Search failed!")
                    console.print(f"\n[red]✗ Search failed![/red]")
                    return None
                    
            except Exception as e:
                progress.update(task, description="Search error!")
                console.print(f"\n[red]✗ Search error: {e}[/red]")
                return None
    
    async def display_results(self, session_id: int):
        """Display search results"""
        console.print(f"\n[bold green]Search Results for Session {session_id}[/bold green]")
        
        # Get session summary
        summary = await self.search_service.get_session_summary(session_id)
        if not summary:
            console.print("[red]Failed to get session summary[/red]")
            return
        
        # Display summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"Original Query: {summary['original_query']}")
        console.print(f"Status: {summary['status']}")
        console.print(f"Total Results: {summary['total_results']}")
        console.print(f"Downloaded: {summary['downloaded_count']}")
        console.print(f"Failed: {summary['failed_count']}")
        
        # Display language statistics
        if summary['language_stats']:
            lang_table = Table(title="Results by Language")
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Count", style="magenta")
            
            for lang, count in summary['language_stats'].items():
                lang_name = config.LANGUAGE_NAMES.get(lang, lang)
                lang_table.add_row(lang_name, str(count))
            
            console.print(lang_table)
        
        # Display engine statistics
        if summary['engine_stats']:
            engine_table = Table(title="Results by Search Engine")
            engine_table.add_column("Engine", style="cyan")
            engine_table.add_column("Count", style="magenta")
            
            for engine, count in summary['engine_stats'].items():
                engine_table.add_row(engine, str(count))
            
            console.print(engine_table)
    
    async def export_results(self, session_id: int, export_format: str = 'csv'):
        """Export search results"""
        console.print(f"\n[bold green]Exporting Results for Session {session_id}[/bold green]")
        
        if export_format in ['csv', 'both']:
            # Export to CSV
            csv_path = await self.search_service.export_results(session_id, 'csv')
            if csv_path:
                console.print(f"[green]✓ CSV exported to: {csv_path}[/green]")
        
        if export_format in ['excel', 'both']:
            # Export to Excel
            excel_path = await self.search_service.export_results(session_id, 'excel')
            if excel_path:
                console.print(f"[green]✓ Excel exported to: {excel_path}[/green]")
    
    def display_storage_stats(self):
        """Display storage statistics"""
        stats = self.file_manager.get_storage_stats()
        
        console.print(f"\n[bold green]Storage Statistics[/bold green]")
        console.print(f"Total Sessions: {stats['total_sessions']}")
        console.print(f"Total Files: {stats['total_files']}")
        console.print(f"Total Size: {stats['total_size'] / (1024*1024):.2f} MB")
        console.print(f"Date Directories: {stats['date_directories']}")
        
        # Display Redis deduplication stats
        self.display_redis_stats()
    
    def display_redis_stats(self):
        """Display Redis deduplication statistics"""
        try:
            redis_manager = get_redis_manager()
            if not redis_manager.is_available():
                console.print(f"\n[bold yellow]Redis Status:[/bold yellow] [red]Not Available[/red]")
                console.print("[dim]Deduplication is disabled. Install Redis for duplicate detection.[/dim]")
                return
            
            stats = redis_manager.get_duplicate_stats()
            console.print(f"\n[bold green]Redis Deduplication Statistics[/bold green]")
            console.print(f"Total processed URLs: {stats.get('total_processed', 0)}")
            console.print(f"Unique URLs: {stats.get('unique_urls', 0)}")
            console.print(f"Active sessions: {stats.get('active_sessions', 0)}")
            console.print(f"[bold green]Redis Status:[/bold green] [green]Available[/green]")
            
        except Exception as e:
            console.print(f"[red]Error getting Redis stats: {e}[/red]")

@click.command()
@click.option('--query', '-q', help='Search topic/subject')
@click.option('--criteria', '-c', help='Filter criteria for AI analysis')
@click.option('--max-results', '-m', default=20, help='Max results per engine')
@click.option('--export-format', '-f', type=click.Choice(['csv', 'excel', 'both']), default='csv', help='Export format (default: csv)')
@click.option('--languages', '-l', help='Additional languages for search (comma-separated, e.g., "vi,ja,ko"). Default: search in original language only.')
@click.option('--session-id', '-s', type=int, help='Session ID to view results')
@click.option('--stats', is_flag=True, help='Show storage statistics')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--ai-analysis', '-a', is_flag=True, default=True, help='Enable AI content analysis (default: enabled)')
@click.option('--no-ai', is_flag=True, help='Disable AI content analysis')
@click.option('--enable-ai-optimization', is_flag=True, default=False, help='Enable AI query optimization (default: disabled)')
@click.option('--search-pages', '-p', default=1, help='Number of search pages to fetch (default: 1, max: 3)')
@click.option('--aggressive-search', is_flag=True, help='Use aggressive search settings for maximum results')
def main(query, criteria, max_results, export_format, languages, session_id, stats, interactive, ai_analysis, no_ai, enable_ai_optimization, search_pages, aggressive_search):
    """Documentation Collection - Multi-language document search and collection"""
    
    cli = DocumentationCollectionCLI()
    
    # Test database connection
    if not db_manager.test_connection():
        console.print("[red]✗ Database connection failed![/red]")
        console.print("Please check your database configuration in .env file")
        return
    
    # Display banner
    cli.display_banner()
    
    # Show storage stats
    if stats:
        cli.display_storage_stats()
        return
    
    # Prepare search criteria for async operations
    search_criteria = None
    if query:
        console.print(f"[bold green]Searching for topic: {query}[/bold green]")
        if criteria:
            console.print(f"[bold blue]Filter criteria: {criteria}[/bold blue]")
        
        # Parse additional languages
        additional_languages = []
        if languages:
            additional_languages = [lang.strip() for lang in languages.split(',') if lang.strip()]
        
        # Handle AI analysis flags
        final_ai_analysis = ai_analysis and not no_ai
        
        # Ensure max_results has a default value
        max_results = max_results or 20
        
        # Handle aggressive search settings
        if aggressive_search:
            # Aggressive search: use all languages, more results, multiple pages
            if not additional_languages:
                additional_languages = ['en', 'vi', 'ja', 'ko', 'ru', 'fa']  # All supported languages
            max_results = max(max_results, 30)  # Minimum 30 results per engine
            search_pages = max(search_pages, 2)  # Minimum 2 pages
            console.print(f"[yellow]🔍 Aggressive search enabled: {max_results} results/engine, {search_pages} pages, {len(additional_languages)} languages[/yellow]")
        
        search_criteria = {
            'max_results_per_engine': max_results,
            'user_input': False,
            'filter_criteria': criteria,
            'ai_analysis': final_ai_analysis,
            'ai_optimization': enable_ai_optimization,
            'additional_languages': additional_languages,
            'search_pages': search_pages,
            'aggressive_search': aggressive_search
        }
    
    async def main_async():
        # View existing session
        if session_id:
            await cli.display_results(session_id)
            if export_format in ['csv', 'excel', 'both']:
                await cli.export_results(session_id, export_format)
            return
        
        # Interactive mode
        if interactive or not query:
            cli.display_supported_languages()
            cli.display_search_engines()
            
            current_session_id = await cli.search_documents_interactive()
            if current_session_id:
                await cli.display_results(current_session_id)
                await cli.export_results(current_session_id, export_format)
            return
        
        # Command line mode
        if query:
            current_session_id = await cli.search_service.search_documents(query, search_criteria)
            if current_session_id:
                console.print(f"[green]✓ Search completed! Session ID: {current_session_id}[/green]")
                await cli.display_results(current_session_id)
                await cli.export_results(current_session_id, export_format)
            else:
                console.print("[red]✗ Search failed![/red]")
    
    # Run async operations
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
