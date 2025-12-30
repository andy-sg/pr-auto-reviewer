import 'dotenv/config';

export const config = {
  // GitHub
  githubToken: process.env.GITHUB_TOKEN || '',

  // Vertex AI (for Gemini)
  vertexProjectId: process.env.VERTEX_AI_PROJECT_ID || '',
  vertexLocation: process.env.VERTEX_AI_LOCATION || 'us-central1',

  // Model Selection
  defaultModel: process.env.DEFAULT_MODEL || 'gemini',
};

export function validateConfig(): void {
  if (!config.githubToken) {
    throw new Error('GITHUB_TOKEN is required');
  }

  if (config.defaultModel === 'gemini' && !config.vertexProjectId) {
    throw new Error('VERTEX_AI_PROJECT_ID is required for Gemini model');
  }
}
