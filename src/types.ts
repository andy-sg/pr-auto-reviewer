export interface PRContext {
  title: string;
  description: string;
  number: number;
  baseBranch: string;
  headBranch: string;
  state: string;
  author: string;
}

export interface ReviewComment {
  id: number;
  body: string;
  path: string;
  position: number | null;
  line: number | null;
  originalLine: number | null;
  commitId: string;
  user: string;
  createdAt: Date;
  inReplyToId: number | null;
}

export interface FixResult {
  success: boolean;
  filePath: string;
  changesMade: string;
  error?: string;
  reasoning?: string;
}

export interface AnalysisResult {
  action: 'modify' | 'create' | 'delete' | 'no_action';
  reasoning: string;
  changes: string[];
}

export interface PendingReply {
  comment: ReviewComment;
  reply: string;
  result: FixResult;
}
