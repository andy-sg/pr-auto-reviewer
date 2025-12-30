import type { AnalysisResult, PRContext } from '../types.js';

export interface AIModel {
  analyzeReview(
    fileContent: string,
    filePath: string,
    reviewComment: string,
    prContext: PRContext
  ): Promise<AnalysisResult>;

  generateCodeFix(
    fileContent: string,
    filePath: string,
    reviewComment: string,
    lineNumber?: number
  ): Promise<string>;

  generateReply(reviewComment: string, changesMade: string): Promise<string>;
}
