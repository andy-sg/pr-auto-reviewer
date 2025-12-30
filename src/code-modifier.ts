import * as fs from 'fs/promises';
import * as path from 'path';
import type { AIModel } from './models/index.js';
import type { FixResult, PRContext } from './types.js';

export class CodeModifier {
  constructor(
    private model: AIModel,
    private repoPath: string
  ) {}

  async applyFix(
    filePath: string,
    reviewComment: string,
    prContext: PRContext,
    lineNumber?: number
  ): Promise<FixResult> {
    const fullPath = path.join(this.repoPath, filePath);

    // Check if file exists
    try {
      await fs.access(fullPath);
    } catch {
      return {
        success: false,
        filePath,
        changesMade: '',
        error: `File not found: ${filePath}`,
      };
    }

    // Read current file content
    let currentContent: string;
    try {
      currentContent = await fs.readFile(fullPath, 'utf-8');
    } catch (e) {
      return {
        success: false,
        filePath,
        changesMade: '',
        error: `Failed to read file: ${e}`,
      };
    }

    // Analyze what needs to be done
    const analysis = await this.model.analyzeReview(
      currentContent,
      filePath,
      reviewComment,
      prContext
    );

    if (analysis.action === 'no_action') {
      return {
        success: true,
        filePath,
        changesMade: 'No changes needed',
        reasoning: analysis.reasoning,
      };
    }

    // Generate fixed code
    try {
      const fixedContent = await this.model.generateCodeFix(
        currentContent,
        filePath,
        reviewComment,
        lineNumber
      );

      // Write fixed content back to file
      await fs.writeFile(fullPath, fixedContent, 'utf-8');

      let changesSummary = `Applied fix: ${analysis.reasoning}`;
      if (analysis.changes.length > 0) {
        changesSummary += '\n- ' + analysis.changes.join('\n- ');
      }

      return {
        success: true,
        filePath,
        changesMade: changesSummary,
        reasoning: analysis.reasoning,
      };
    } catch (e) {
      return {
        success: false,
        filePath,
        changesMade: '',
        error: `Failed to apply fix: ${e}`,
      };
    }
  }
}
