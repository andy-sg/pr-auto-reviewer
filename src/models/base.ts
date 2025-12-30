import type { AnalysisResult, PRContext, ReviewSuggestion } from '../types.js';

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

  reviewCode(
    filePath: string,
    patch: string,
    prContext: PRContext
  ): Promise<ReviewSuggestion[]>;
}
