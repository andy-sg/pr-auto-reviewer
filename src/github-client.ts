import { Octokit } from 'octokit';
import { config } from './config.js';
import type { PRContext, ReviewComment, PRFile, ReviewSuggestion } from './types.js';

export class GitHubClient {
  private octokit: Octokit;

  constructor() {
    this.octokit = new Octokit({ auth: config.githubToken });
  }

  parsePrUrl(prUrl: string): { owner: string; repo: string; prNumber: number } {
    const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
    if (!match) {
      throw new Error(`Invalid PR URL: ${prUrl}`);
    }
    return {
      owner: match[1],
      repo: match[2],
      prNumber: parseInt(match[3], 10),
    };
  }

  async getPullRequest(prUrl: string) {
    const { owner, repo, prNumber } = this.parsePrUrl(prUrl);
    const { data } = await this.octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
    });
    return { data, owner, repo, prNumber };
  }

  async getPrContext(prUrl: string): Promise<PRContext> {
    const { data } = await this.getPullRequest(prUrl);
    return {
      title: data.title,
      description: data.body || '',
      number: data.number,
      baseBranch: data.base.ref,
      headBranch: data.head.ref,
      state: data.state,
      author: data.user?.login || 'unknown',
    };
  }

  async getReviewComments(prUrl: string): Promise<ReviewComment[]> {
    const { owner, repo, prNumber } = this.parsePrUrl(prUrl);
    const { data } = await this.octokit.rest.pulls.listReviewComments({
      owner,
      repo,
      pull_number: prNumber,
    });

    return data.map((comment) => ({
      id: comment.id,
      body: comment.body,
      path: comment.path,
      position: comment.position ?? null,
      line: comment.line ?? null,
      originalLine: comment.original_line ?? null,
      commitId: comment.commit_id,
      user: comment.user?.login || 'unknown',
      createdAt: new Date(comment.created_at),
      inReplyToId: comment.in_reply_to_id ?? null,
    }));
  }

  async getFileContent(prUrl: string, filePath: string): Promise<string> {
    const { owner, repo, data: pr } = await this.getPullRequest(prUrl);
    const { data } = await this.octokit.rest.repos.getContent({
      owner,
      repo,
      path: filePath,
      ref: pr.head.sha,
    });

    if ('content' in data && data.content) {
      return Buffer.from(data.content, 'base64').toString('utf-8');
    }
    throw new Error(`Could not fetch file ${filePath}`);
  }

  async postReviewCommentReply(
    prUrl: string,
    commentId: number,
    replyText: string
  ): Promise<void> {
    const { owner, repo, prNumber } = this.parsePrUrl(prUrl);
    await this.octokit.rest.pulls.createReplyForReviewComment({
      owner,
      repo,
      pull_number: prNumber,
      comment_id: commentId,
      body: replyText,
    });
  }

  async getPrFiles(prUrl: string): Promise<PRFile[]> {
    const { owner, repo, prNumber } = this.parsePrUrl(prUrl);
    const { data } = await this.octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: prNumber,
    });

    return data.map((file) => ({
      filename: file.filename,
      status: file.status,
      additions: file.additions,
      deletions: file.deletions,
      changes: file.changes,
      patch: file.patch,
      contentsUrl: file.contents_url,
    }));
  }

  async createReview(
    prUrl: string,
    comments: ReviewSuggestion[],
    body?: string
  ): Promise<void> {
    const { owner, repo, prNumber, data: pr } = await this.getPullRequest(prUrl);

    if (comments.length === 0 && !body) {
      return;
    }

    const reviewComments = comments.map((c) => ({
      path: c.path,
      line: c.line,
      body: c.body,
      side: c.side || ('RIGHT' as const),
    }));

    await this.octokit.rest.pulls.createReview({
      owner,
      repo,
      pull_number: prNumber,
      commit_id: pr.head.sha,
      body: body || '',
      event: 'COMMENT',
      comments: reviewComments,
    });
  }
}
