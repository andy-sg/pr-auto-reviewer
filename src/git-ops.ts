import { simpleGit, SimpleGit } from 'simple-git';

export class GitOperations {
  private git: SimpleGit;

  constructor(repoPath: string) {
    this.git = simpleGit(repoPath);
  }

  async commitAndPush(filePaths: string[], commitMessage: string): Promise<string> {
    // Add files
    await this.git.add(filePaths);

    // Commit
    const commitResult = await this.git.commit(commitMessage);
    const commitSha = commitResult.commit;

    // Push
    await this.git.push();

    return commitSha;
  }

  async getCurrentBranch(): Promise<string> {
    const branch = await this.git.revparse(['--abbrev-ref', 'HEAD']);
    return branch.trim();
  }

  async hasChanges(): Promise<boolean> {
    const status = await this.git.status();
    return status.modified.length > 0 || status.created.length > 0;
  }
}
