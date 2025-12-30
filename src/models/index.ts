import type { AIModel } from './base.js';
import { GeminiModel } from './gemini.js';
import { config } from '../config.js';

export function getModel(): AIModel {
  const modelName = config.defaultModel;

  switch (modelName) {
    case 'gemini':
      return new GeminiModel();
    default:
      throw new Error(`Unknown model: ${modelName}`);
  }
}

export type { AIModel };
