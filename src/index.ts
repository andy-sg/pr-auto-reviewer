#!/usr/bin/env node

import { Command } from 'commander';
import { select, checkbox, input, confirm } from '@inquirer/prompts';
import chalk from 'chalk';
import ora from 'ora';

import { config, validateConfig } from './config.js';
import { GitHubClient } from './github-client.js';
import { getModel } from './models/index.js';
import { CodeModifier } from './code-modifier.js';
import { GitOperations } from './git-ops.js';
import type { ReviewComment, PendingReply, FixResult } from './types.js';

const program = new Command();

program
  .name('pr-fix')
  .description('Automatically fix code based on PR review comments')
  .version('1.0.0')
  .argument('<pr-url>', 'GitHub Pull Request URL')
  .option('--repo-path <path>', 'Path to local repository', '.')
  .option('--dry-run', 'Show what would be done without making changes')
  .option('--no-auto-reply', 'Disable automatic replies to comments')
  .showHelpAfterError(true)
  .action(async (prUrl: string, options) => {
    await runFixMode(prUrl, options);
  });

async function runFixMode(
  prUrl: string,
  options: { repoPath: string; dryRun?: boolean; autoReply?: boolean }
) {
  console.log(chalk.cyan.bold('\n🔧 PR Auto Reviewer - Fix Mode\n'));

  try {
    // Validate configuration
    validateConfig();

    console.log(chalk.bold(`Using AI model: ${config.defaultModel}`));

    // Initialize components
    const githubClient = new GitHubClient();
    const aiModel = getModel();
    const codeModifier = new CodeModifier(aiModel, options.repoPath);
    const gitOps = new GitOperations(options.repoPath);

    // Get PR information
    const spinner = ora('Fetching PR information...').start();
    const prContext = await githubClient.getPrContext(prUrl);
    spinner.succeed('PR information fetched');

    console.log(chalk.bold(`\nPR: #${prContext.number} - ${prContext.title}`));
    console.log(chalk.bold(`Branch: ${prContext.headBranch} → ${prContext.baseBranch}\n`));

    // Get review comments
    spinner.start('Fetching review comments...');
    const comments = await githubClient.getReviewComments(prUrl);
    spinner.succeed('Review comments fetched');

    if (comments.length === 0) {
      console.log(chalk.yellow('\n리뷰 코멘트가 없습니다!'));
      return;
    }

    console.log(chalk.bold(`\nFound ${comments.length} review comment(s)\n`));

    // Display all comments
    console.log(chalk.bold('리뷰 코멘트 목록:\n'));

    comments.forEach((comment, idx) => {
      const preview = comment.body.split('\n')[0].slice(0, 80);
      const ellipsis = comment.body.split('\n')[0].length > 80 ? '...' : '';
      console.log(`  ${idx + 1}. [${comment.user}] ${comment.path}:${comment.line || '?'}`);
      console.log(chalk.dim(`     ${preview}${ellipsis}`));
    });

    console.log();

    // Ask how to process
    const selectionMode = await select({
      message: '어떻게 처리할까요?',
      choices: [
        { name: '✓ 모든 코멘트 처리', value: 'all' },
        { name: '☐ 특정 코멘트만 선택', value: 'select' },
        { name: '✗ 취소', value: 'cancel' },
      ],
    });

    if (selectionMode === 'cancel') {
      console.log(chalk.yellow('취소되었습니다.'));
      return;
    }

    let selectedComments: ReviewComment[];

    if (selectionMode === 'all') {
      selectedComments = comments;
    } else {
      const choices = comments.map((comment, idx) => {
        const preview = comment.body.split('\n')[0].slice(0, 60);
        const ellipsis = comment.body.split('\n')[0].length > 60 ? '...' : '';
        return {
          name: `[${comment.user}] ${comment.path}:${comment.line || '?'} - ${preview}${ellipsis}`,
          value: idx,
        };
      });

      const selectedIndices = await checkbox({
        message: '수정할 코멘트를 선택하세요 (Space로 선택, Enter로 확인):',
        choices,
      });

      if (selectedIndices.length === 0) {
        console.log(chalk.yellow('선택된 코멘트가 없습니다. 종료합니다.'));
        return;
      }

      selectedComments = selectedIndices.map((i) => comments[i]);
    }

    console.log(chalk.bold(`\n${selectedComments.length}개의 코멘트가 선택되었습니다.\n`));

    // Process each comment
    const modifiedFiles: string[] = [];
    const results: FixResult[] = [];
    const pendingReplies: PendingReply[] = [];

    for (let idx = 0; idx < selectedComments.length; idx++) {
      const comment = selectedComments[idx];
      console.log(chalk.cyan.bold(`Comment ${idx + 1}/${selectedComments.length}`));
      console.log(chalk.bold(`File: ${comment.path}`));
      console.log(chalk.bold(`Line: ${comment.line || '?'}`));
      console.log(chalk.bold(`Comment: ${comment.body.slice(0, 100)}...`));

      if (options.dryRun) {
        console.log(chalk.yellow('Dry run mode - skipping actual changes\n'));
        continue;
      }

      // Apply fix
      spinner.start('Analyzing and applying fix...');

      const result = await codeModifier.applyFix(
        comment.path,
        comment.body,
        prContext,
        comment.line || undefined
      );

      spinner.stop();
      results.push(result);

      if (result.success) {
        console.log(chalk.green('✓ Successfully applied fix'));
        console.log(chalk.dim(result.changesMade));
        modifiedFiles.push(comment.path);

        // Generate reply for preview
        if (options.autoReply !== false) {
          try {
            const reply = await aiModel.generateReply(comment.body, result.changesMade);
            pendingReplies.push({ comment, reply, result });
            console.log(chalk.dim('답변이 생성되었습니다 (나중에 미리보기)'));
          } catch (e) {
            console.log(chalk.yellow(`⚠ Failed to generate reply: ${e}`));
          }
        }
      } else {
        console.log(chalk.red('✗ Failed to apply fix'));
        console.log(chalk.red(result.error || 'Unknown error'));
      }

      console.log();
    }

    // Reply preview and editing
    if (pendingReplies.length > 0 && !options.dryRun) {
      console.log('\n' + '='.repeat(50));
      console.log(chalk.cyan.bold('답변 미리보기 및 수정\n'));

      const finalReplies: { comment: ReviewComment; reply: string }[] = [];

      for (let idx = 0; idx < pendingReplies.length; idx++) {
        const pending = pendingReplies[idx];
        const { comment, reply } = pending;

        console.log(chalk.bold(`#${idx + 1} ${comment.path}:${comment.line || '?'}`));
        console.log(chalk.dim(`원본 코멘트: ${comment.body.slice(0, 80)}...`));
        console.log(chalk.green.bold('\n생성된 답변:'));
        console.log(chalk.green(`┌${'─'.repeat(48)}┐`));
        console.log(chalk.green(`│ ${reply.padEnd(47)}│`));
        console.log(chalk.green(`└${'─'.repeat(48)}┘`));

        const action = await select({
          message: '이 답변을 어떻게 처리할까요?',
          choices: [
            { name: '✓ 그대로 사용', value: 'use' },
            { name: '✏ 수정하기', value: 'edit' },
            { name: '✗ 건너뛰기', value: 'skip' },
          ],
        });

        if (action === 'use') {
          finalReplies.push({ comment, reply });
          console.log(chalk.green('✓ 답변이 대기열에 추가되었습니다.\n'));
        } else if (action === 'edit') {
          const editedReply = await input({
            message: '답변을 수정하세요:',
            default: reply,
          });

          if (editedReply) {
            finalReplies.push({ comment, reply: editedReply });
            console.log(chalk.green('✓ 수정된 답변이 대기열에 추가되었습니다.\n'));
          } else {
            console.log(chalk.yellow('답변이 건너뛰어졌습니다.\n'));
          }
        } else {
          console.log(chalk.yellow('답변이 건너뛰어졌습니다.\n'));
        }
      }

      // Post all confirmed replies
      if (finalReplies.length > 0) {
        console.log(chalk.bold(`\n${finalReplies.length}개의 답변을 게시합니다...`));

        for (const item of finalReplies) {
          try {
            await githubClient.postReviewCommentReply(prUrl, item.comment.id, item.reply);
            console.log(chalk.green(`✓ Posted reply to ${item.comment.path}:${item.comment.line || '?'}`));
          } catch (e) {
            console.log(chalk.yellow(`⚠ Failed to post reply: ${e}`));
          }
        }
      }
    }

    // Commit and push changes
    if (modifiedFiles.length > 0 && !options.dryRun) {
      console.log(chalk.bold('\nCommitting and pushing changes...'));

      try {
        const uniqueFiles = [...new Set(modifiedFiles)];
        const commitMessage = `fix: Apply review feedback from PR #${prContext.number}\n\nAutomatically applied fixes for ${selectedComments.length} review comment(s)`;

        const commitSha = await gitOps.commitAndPush(uniqueFiles, commitMessage);
        console.log(chalk.green('✓ Committed and pushed changes'));
        console.log(chalk.dim(`Commit: ${commitSha.slice(0, 7)}`));
      } catch (e) {
        console.log(chalk.red(`✗ Failed to commit/push: ${e}`));
        process.exit(1);
      }
    }

    // Summary
    console.log('\n' + '='.repeat(50));
    console.log(chalk.cyan.bold('Summary\n'));

    const successful = results.filter((r) => r.success).length;
    const failed = results.length - successful;

    console.log(chalk.green(`Successful: ${successful}`));
    console.log(chalk.red(`Failed: ${failed}`));
    console.log(chalk.blue(`Total: ${results.length}`));

    if (options.dryRun) {
      console.log(chalk.yellow('\nThis was a dry run - no actual changes were made'));
    }
  } catch (e) {
    console.error(chalk.red(`\nError: ${e}`));
    console.log();
    program.help();
  }
}

program.parse();
