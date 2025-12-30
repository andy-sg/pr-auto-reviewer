import { VertexAI } from '@google-cloud/vertexai';
import { config } from '../config.js';
import type { AIModel } from './base.js';
import type { AnalysisResult, PRContext } from '../types.js';

export class GeminiModel implements AIModel {
  private model;

  constructor() {
    const vertexAI = new VertexAI({
      project: config.vertexProjectId,
      location: config.vertexLocation,
    });
    this.model = vertexAI.getGenerativeModel({
      model: 'gemini-2.0-flash-001',
    });
  }

  async analyzeReview(
    fileContent: string,
    filePath: string,
    reviewComment: string,
    prContext: PRContext
  ): Promise<AnalysisResult> {
    const prompt = `You are a code review assistant. Analyze this review comment and determine what changes need to be made.

PR Context:
- Title: ${prContext.title}
- Description: ${prContext.description}

File: ${filePath}
Review Comment: ${reviewComment}

Current File Content:
\`\`\`
${fileContent}
\`\`\`

Analyze the review and respond in JSON format with:
{
    "action": "modify|create|delete|no_action",
    "reasoning": "explanation of what needs to be done",
    "changes": ["list of specific changes to make"]
}`;

    const result = await this.model.generateContent(prompt);
    const text = result.response.candidates?.[0]?.content?.parts?.[0]?.text || '';

    try {
      const startIdx = text.indexOf('{');
      const endIdx = text.lastIndexOf('}') + 1;
      if (startIdx !== -1 && endIdx > startIdx) {
        const jsonStr = text.slice(startIdx, endIdx);
        return JSON.parse(jsonStr);
      }
    } catch {
      // ignore parse error
    }

    return {
      action: 'no_action',
      reasoning: 'Could not parse response',
      changes: [],
    };
  }

  async generateCodeFix(
    fileContent: string,
    filePath: string,
    reviewComment: string,
    lineNumber?: number
  ): Promise<string> {
    const lineInfo = lineNumber ? `at line ${lineNumber}` : '';

    const prompt = `You are a code review assistant. Fix the code based on this review comment.

File: ${filePath} ${lineInfo}
Review Comment: ${reviewComment}

Current File Content:
\`\`\`
${fileContent}
\`\`\`

Please provide the COMPLETE fixed file content. Return ONLY the fixed code without any explanation or markdown formatting.`;

    const result = await this.model.generateContent(prompt);
    let fixedCode = result.response.candidates?.[0]?.content?.parts?.[0]?.text || '';
    fixedCode = fixedCode.trim();

    // Remove markdown code blocks if present
    if (fixedCode.startsWith('```')) {
      const lines = fixedCode.split('\n');
      lines.shift(); // Remove first line (```language)
      if (lines[lines.length - 1]?.trim() === '```') {
        lines.pop(); // Remove last line (```)
      }
      fixedCode = lines.join('\n');
    }

    return fixedCode;
  }

  async generateReply(reviewComment: string, changesMade: string): Promise<string> {
    const prompt = `리뷰 코멘트에 대한 간단하고 전문적인 답변을 생성하세요.

리뷰 코멘트: ${reviewComment}
적용된 변경사항: ${changesMade}

피드백에 감사하고 변경사항을 확인하는 짧은 답변(1-2문장)을 작성하세요.
전문적이고 간결하게 작성하세요. 마크다운 포맷팅은 사용하지 마세요.
반드시 한국어로 작성하세요.`;

    const result = await this.model.generateContent(prompt);
    return result.response.candidates?.[0]?.content?.parts?.[0]?.text?.trim() || '';
  }
}
