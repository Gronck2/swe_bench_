"""
Command-line interface for SWE-bench data point validator.
"""

import click
import sys
from pathlib import Path

from .validator import SWEBenchValidator, ValidationResult
from .config import ValidationConfig
from .utils import setup_logging

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--log-file", type=Path, help="Log file path")
@click.pass_context
def cli(ctx, verbose, log_file):
    """SWE-bench Data Point Validator CLI"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Setup logging
    setup_logging(verbose=verbose, log_file=log_file)


@cli.command()
@click.argument("file_path", type=Path)
@click.option("--timeout", type=int, help="Evaluation timeout in seconds")
@click.pass_context
def validate_file(ctx, file_path, timeout):
    """Validate a single data point file using SWE-bench evaluation harness."""
    
    if not file_path.exists():
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)
    
    # Create config
    config = ValidationConfig()
    if timeout:
        config.default_timeout = timeout
    
    # Create validator
    validator = SWEBenchValidator(config)
    
    click.echo(f"Validating data point: {file_path}")
    click.echo("Using SWE-bench evaluation harness...")
    
    # Run validation
    result = validator.validate_single_file(file_path)
    
    # Display result
    if result.success:
        click.echo(f"✅ PASSED: {result.instance_id}", color=True)
    else:
        click.echo(f"❌ FAILED: {result.instance_id}", color=True)
        if result.error_message:
            click.echo(f"   Error: {result.error_message}")
        sys.exit(1)


@cli.command()
@click.argument("directory", type=Path, default=Path("data_points"))
@click.option("--pattern", default="*.json", help="File pattern to match")
@click.option("--timeout", type=int, help="Evaluation timeout in seconds")
@click.pass_context
def validate_directory(ctx, directory, pattern, timeout):
    """Validate all data point files in a directory."""
    
    if not directory.exists():
        click.echo(f"Error: Directory not found: {directory}", err=True)
        sys.exit(1)
    
    # Find files
    files = list(directory.glob(pattern))
    if not files:
        click.echo(f"No files found matching {pattern} in {directory}")
        return
    
    # Create config
    config = ValidationConfig()
    if timeout:
        config.default_timeout = timeout
    
    # Create validator
    validator = SWEBenchValidator(config)
    
    click.echo(f"Found {len(files)} data point files")
    click.echo("Using SWE-bench evaluation harness...")
    
    # Validate each file
    results = []
    for i, file_path in enumerate(files, 1):
        click.echo(f"\n[{i}/{len(files)}] Validating: {file_path.name}")
        result = validator.validate_single_file(file_path)
        results.append(result)
        
        if result.success:
            click.echo(f"   ✅ PASSED")
        else:
            click.echo(f"   ❌ FAILED: {result.error_message}")
    
    # Summary
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    
    click.echo(f"\n📊 Summary:")
    click.echo(f"   Total: {len(results)}")
    click.echo(f"   Passed: {passed}")
    click.echo(f"   Failed: {failed}")
    click.echo(f"   Success Rate: {passed/len(results)*100:.1f}%")
    
    if failed > 0:
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()
