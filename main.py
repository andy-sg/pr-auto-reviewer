#!/usr/bin/env python3
"""PR Auto Reviewer - Automatically fix code based on PR reviews."""
import os
import sys
import click
import questionary
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from github_client import GitHubClient
from models.claude import ClaudeModel
from models.claude_code import ClaudeCodeModel
from models.gemini import GeminiModel
from code_modifier import CodeModifier
from code_reviewer import CodeReviewer
from git_ops import GitOperations

console = Console()


def get_model(model_name: str):
    """Get AI model instance based on name."""
    if model_name == 'claude':
        return ClaudeModel()
    elif model_name == 'claude-code':
        return ClaudeCodeModel()
    elif model_name == 'gemini':
        return GeminiModel()
    else:
        raise ValueError(f"Unknown model: {model_name}")


@click.command()
@click.argument('pr_url')
@click.option('--mode', type=click.Choice(['review', 'fix']), default='fix', help='Mode: review (AI reviews PR) or fix (AI fixes review comments)')
@click.option('--model', default=None, help='AI model to use (claude, claude-code, or gemini)')
@click.option('--repo-path', default='.', help='Path to local repository')
@click.option('--auto-reply', is_flag=True, default=True, help='Automatically reply to review comments')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--min-severity', type=click.Choice(['critical', 'major', 'minor']), default=None, help='Minimum severity level to include (if not specified, will ask interactively)')
def main(pr_url: str, mode: str, model: str, repo_path: str, auto_reply: bool, dry_run: bool, min_severity: str):
    """
    Automatically fix code based on PR review comments.

    PR_URL: GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)
    """
    console.print(Panel.fit(
        "[bold cyan]PR Auto Reviewer[/bold cyan]\n"
        "Automatically applying fixes from code reviews",
        border_style="cyan"
    ))

    try:
        # Validate configuration
        Config.validate()

        # Determine which model to use
        model_name = model or Config.DEFAULT_MODEL
        console.print(f"[bold]Using AI model:[/bold] {model_name}")

        # Initialize components
        console.print("[bold]Initializing...[/bold]")
        github_client = GitHubClient()
        ai_model = get_model(model_name)

        # Get PR information
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching PR information...", total=None)
            pr = github_client.get_pull_request(pr_url)
            pr_context = github_client.get_pr_context(pr)
            progress.update(task, completed=True)

        console.print(f"\n[bold]PR:[/bold] #{pr_context['number']} - {pr_context['title']}")
        console.print(f"[bold]Branch:[/bold] {pr_context['head_branch']} → {pr_context['base_branch']}")
        console.print(f"[bold]Mode:[/bold] {mode.upper()}\n")

        # Branch based on mode
        if mode == 'review':
            run_review_mode(pr, pr_context, github_client, ai_model, dry_run, min_severity)
        else:
            # Initialize fix mode specific components
            code_modifier = CodeModifier(ai_model, repo_path)
            git_ops = GitOperations(repo_path)
            run_fix_mode(pr, pr_context, github_client, ai_model, code_modifier, git_ops, repo_path, auto_reply, dry_run)

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        sys.exit(1)


def run_review_mode(pr, pr_context, github_client, ai_model, dry_run, min_severity=None):
    """Run in review mode - AI reviews the PR and posts comments."""
    console.print("[bold cyan]AI Code Review Mode[/bold cyan]\n")

    # Ask for severity filter interactively if not specified
    if min_severity is None:
        choices = questionary.checkbox(
            '어떤 severity 레벨의 코멘트를 포함할까요?',
            choices=[
                questionary.Choice('🔴 CRITICAL (필수 수정: 버그, 보안 취약점 등)', value='critical', checked=True),
                questionary.Choice('🟡 MAJOR (권장 수정: 잠재적 버그, 에러 처리 누락 등)', value='major', checked=True),
                questionary.Choice('⚪️ MINOR (참고용: 네이밍, 스타일 등)', value='minor', checked=False),
            ]
        ).ask()

        if not choices:
            console.print("[yellow]선택이 취소되었습니다.[/yellow]")
            return

        # Determine minimum severity based on selections
        if 'minor' in choices:
            min_severity = 'minor'
        elif 'major' in choices:
            min_severity = 'major'
        elif 'critical' in choices:
            min_severity = 'critical'
        else:
            console.print("[yellow]최소 하나의 severity를 선택해야 합니다.[/yellow]")
            return

    # Show severity filter
    severity_info = {
        'critical': '🔴 CRITICAL만',
        'major': '🔴 CRITICAL + 🟡 MAJOR',
        'minor': '🔴 CRITICAL + 🟡 MAJOR + ⚪️ MINOR'
    }
    console.print(f"[bold]Severity 필터:[/bold] {severity_info[min_severity]}\n")

    # Initialize code reviewer
    code_reviewer = CodeReviewer(ai_model)

    # Get PR files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching PR files...", total=None)
        files = github_client.get_pr_files(pr)
        progress.update(task, completed=True)

    console.print(f"[bold]Found {len(files)} changed file(s)[/bold]\n")

    if not files:
        console.print("[yellow]No files to review![/yellow]")
        return

    # Filter files with patches
    files_to_review = [f for f in files if f['patch']]
    skipped = len(files) - len(files_to_review)
    if skipped > 0:
        console.print(f"[dim]Skipping {skipped} file(s) (binary or no diff)[/dim]\n")

    if not files_to_review:
        console.print("[yellow]No files with diffs to review![/yellow]")
        return

    if dry_run:
        console.print("[yellow]Dry run mode - skipping review generation[/yellow]\n")
        return

    # Review files in parallel
    all_comments = []
    patches = {}  # Store patches for validation

    def review_file(file_info):
        """Review a single file."""
        filename = file_info['filename']
        patch = file_info['patch']

        try:
            file_content = github_client.get_file_content(pr, filename)
        except Exception as e:
            return filename, None, str(e)

        try:
            comments = code_reviewer.analyze_file_changes(
                file_path=filename,
                patch=patch,
                file_content=file_content,
                pr_context=pr_context
            )
            return filename, comments, None
        except Exception as e:
            return filename, None, str(e)

    # Use ThreadPoolExecutor for parallel execution
    console.print(f"[bold]Reviewing {len(files_to_review)} file(s) in parallel...[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(
            f"Analyzing files...",
            total=len(files_to_review)
        )

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {
                executor.submit(review_file, file_info): file_info
                for file_info in files_to_review
            }

            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                filename = file_info['filename']
                patch = file_info['patch']

                filename, comments, error = future.result()

                if error:
                    console.print(f"[yellow]⚠ Error reviewing {filename}: {error}[/yellow]")
                elif comments:
                    # Filter comments by severity
                    severity_levels = {'critical': 0, 'major': 1, 'minor': 2}
                    min_level = severity_levels[min_severity]

                    filtered_comments = []
                    for comment in comments:
                        comment_severity = comment.get('severity', 'minor').lower()
                        comment_level = severity_levels.get(comment_severity, 2)

                        if comment_level <= min_level:
                            comment['path'] = filename
                            filtered_comments.append(comment)

                    if filtered_comments:
                        console.print(f"[green]✓ {filename}: {len(filtered_comments)} suggestion(s) (filtered from {len(comments)})[/green]")
                        all_comments.extend(filtered_comments)
                        patches[filename] = patch
                    else:
                        console.print(f"[dim]✓ {filename}: No issues found (all filtered)[/dim]")
                else:
                    console.print(f"[dim]✓ {filename}: No issues found[/dim]")

                progress.update(task, advance=1)

    console.print()

    # Review MINOR issues if they were included
    if all_comments and min_severity == 'minor':
        minor_comments = [c for c in all_comments if c.get('severity', '').lower() == 'minor']

        if minor_comments:
            console.print(f"\n[bold yellow]⚪️ MINOR 이슈 {len(minor_comments)}개가 발견되었습니다.[/bold yellow]")
            console.print("[dim]각 이슈를 확인하고 포함할 항목을 선택하세요.[/dim]\n")

            # Create choices for each minor comment
            choices = []
            for idx, comment in enumerate(minor_comments):
                file_path = comment.get('path', 'unknown')
                line = comment.get('line', '?')
                body = comment.get('body', '')

                # Extract first line of body for preview
                preview = body.split('\n')[0][:80]
                if len(body.split('\n')[0]) > 80:
                    preview += '...'

                choice_text = f"{file_path}:{line} - {preview}"
                choices.append(questionary.Choice(
                    title=choice_text,
                    value=idx,
                    checked=False  # Default: not selected
                ))

            if choices:
                selected_indices = questionary.checkbox(
                    'MINOR 이슈 중 포함할 항목을 선택하세요:',
                    choices=choices
                ).ask()

                if selected_indices is not None:
                    # Keep only selected minor comments
                    selected_minor = [minor_comments[i] for i in selected_indices]

                    # Remove all minor comments and add back selected ones
                    all_comments = [c for c in all_comments if c.get('severity', '').lower() != 'minor']
                    all_comments.extend(selected_minor)

                    console.print(f"\n[green]✓ {len(selected_minor)}개의 MINOR 이슈가 선택되었습니다.[/green]")
                else:
                    # User cancelled - remove all minor comments
                    all_comments = [c for c in all_comments if c.get('severity', '').lower() != 'minor']
                    console.print(f"\n[yellow]MINOR 이슈를 모두 제외합니다.[/yellow]")

    # Post review
    if all_comments and not dry_run:
        console.print(f"\n[bold]Posting review with {len(all_comments)} comment(s)...[/bold]")

        try:
            summary = code_reviewer.generate_summary_comment(
                pr_context=pr_context,
                all_comments=all_comments,
                files_reviewed=len(files_to_review)
            )

            github_client.create_review(
                pr=pr,
                comments=all_comments,
                body=summary,
                event="COMMENT",
                patches=patches
            )

            console.print("[green]✓ Review posted successfully![/green]")

        except Exception as e:
            console.print(f"[red]✗ Failed to post review: {str(e)}[/red]")
            sys.exit(1)

    elif all_comments:
        console.print(f"\n[yellow]Dry run - would have posted {len(all_comments)} comment(s)[/yellow]")
    else:
        console.print(f"\n[green]✓ No issues found in any files![/green]")

    # Summary
    console.print("\n" + "="*50)
    console.print("[bold cyan]Review Summary[/bold cyan]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Count")

    table.add_row("Files Reviewed", str(len(files_to_review)))
    table.add_row("Comments Generated", str(len(all_comments)))

    console.print(table)


def run_fix_mode(pr, pr_context, github_client, ai_model, code_modifier, git_ops, repo_path, auto_reply, dry_run):
    """Run in fix mode - AI fixes review comments."""
    console.print("[bold cyan]Auto-Fix Mode[/bold cyan]\n")

    # Get review comments
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching review comments...", total=None)
        comments = github_client.get_review_comments(pr)
        progress.update(task, completed=True)

    if not comments:
        console.print("\n[yellow]No review comments found![/yellow]")
        return

    console.print(f"\n[bold]Found {len(comments)} review comment(s)[/bold]\n")

    # Process each comment
    modified_files = []
    results = []

    for idx, comment in enumerate(comments, 1):
        console.print(f"[bold cyan]Comment {idx}/{len(comments)}[/bold cyan]")
        console.print(f"[bold]File:[/bold] {comment['path']}")
        console.print(f"[bold]Line:[/bold] {comment['line']}")
        console.print(f"[bold]Comment:[/bold] {comment['body'][:100]}...")

        if dry_run:
            console.print("[yellow]Dry run mode - skipping actual changes[/yellow]\n")
            continue

        # Apply fix
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing and applying fix...", total=None)

            result = code_modifier.apply_fix(
                file_path=comment['path'],
                review_comment=comment['body'],
                pr_context=pr_context,
                line_number=comment['line']
            )

            progress.update(task, completed=True)

        results.append(result)

        if result['success']:
            console.print(f"[green]✓ Successfully applied fix[/green]")
            console.print(f"[dim]{result['changes_made']}[/dim]")
            modified_files.append(comment['path'])

            # Reply to comment if enabled
            if auto_reply and not dry_run:
                try:
                    reply = ai_model.generate_reply(
                        review_comment=comment['body'],
                        changes_made=result['changes_made']
                    )
                    github_client.post_review_comment_reply(
                        pr=pr,
                        comment_id=comment['id'],
                        reply_text=reply
                    )
                    console.print(f"[green]✓ Posted reply to comment[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠ Failed to post reply: {str(e)}[/yellow]")
        else:
            console.print(f"[red]✗ Failed to apply fix[/red]")
            console.print(f"[red]{result.get('error', 'Unknown error')}[/red]")

        console.print()

    # Commit and push changes
    if modified_files and not dry_run:
        console.print("[bold]Committing and pushing changes...[/bold]")

        try:
            unique_files = list(set(modified_files))
            commit_message = f"fix: Apply review feedback from PR #{pr_context['number']}\n\n"
            commit_message += f"Automatically applied fixes for {len(comments)} review comment(s)"

            commit_sha = git_ops.commit_and_push(
                file_paths=unique_files,
                commit_message=commit_message
            )

            console.print(f"[green]✓ Committed and pushed changes[/green]")
            console.print(f"[dim]Commit: {commit_sha[:7]}[/dim]")

        except Exception as e:
            console.print(f"[red]✗ Failed to commit/push: {str(e)}[/red]")
            sys.exit(1)

    # Summary
    console.print("\n" + "="*50)
    console.print("[bold cyan]Summary[/bold cyan]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Status")
    table.add_column("Count")

    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    table.add_row("[green]Successful[/green]", str(successful))
    table.add_row("[red]Failed[/red]", str(failed))
    table.add_row("[blue]Total[/blue]", str(len(results)))

    console.print(table)

    if dry_run:
        console.print("\n[yellow]This was a dry run - no actual changes were made[/yellow]")


if __name__ == '__main__':
    main()
