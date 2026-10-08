import { query } from '@anthropic-ai/claude-agent-sdk';
import { REFACTORING_SUGGESTER_PROMPT } from '../prompts/index.js';
import { RefactoringSuggestionSchema, RefactoringSuggestion } from '../types/analysis-results.js';

const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5-20250929';

/**
 * Analyze a file for refactoring opportunities
 * @param file - File path
 * @param content - File content
 * @returns Refactoring suggestions
 */
export async function suggestRefactorings(
  file: string,
  content: string
): Promise<RefactoringSuggestion> {
  const prompt = `${REFACTORING_SUGGESTER_PROMPT}

Analyze this file for refactoring opportunities:

File: ${file}

\`\`\`
${content}
\`\`\`

IMPORTANT: You MUST respond with valid JSON matching this exact structure:
{
  "file": "${file}",
  "suggestions": [
    {
      "type": "extract-function" | "rename" | "modernize" | "simplify" | "pattern-improvement",
      "location": "<location>",
      "impact": "low" | "medium" | "high",
      "description": "<description>",
      "before": "<before code>",
      "after": "<after code>",
      "benefits": "<benefits>"
    }
  ],
  "summary": "<summary>"
}`;

  const result = query({
    prompt,
    options: {
      model,
      allowedTools: []  // No tools needed for code analysis
    }
  });

  let responseText = '';
  for await (const message of result) {
    if (message.type === 'result' && message.subtype === 'success') {
      responseText = message.result;
      break;
    }
  }

  // Extract JSON from the response
  const jsonMatch = responseText.match(/```(?:json)?\n?([\s\S]*?)\n?```/) || [, responseText];
  const jsonText = jsonMatch[1] || responseText;

  try {
    const parsed = JSON.parse(jsonText.trim());
    return RefactoringSuggestionSchema.parse(parsed);
  } catch (error) {
    // Fallback: return minimal valid result
    return {
      file,
      suggestions: [],
      summary: 'Analysis completed but failed to parse structured output'
    };
  }
}
