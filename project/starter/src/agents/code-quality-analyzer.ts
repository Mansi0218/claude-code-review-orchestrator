import { query } from '@anthropic-ai/claude-agent-sdk';
import { CODE_QUALITY_ANALYZER_PROMPT } from '../prompts/index.js';
import { CodeQualityResultSchema, CodeQualityResult } from '../types/analysis-results.js';

const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5-20250929';

/**
 * Analyze a file for code quality issues
 * @param file - File path
 * @param content - File content
 * @returns Code quality analysis result
 */
export async function analyzeCodeQuality(
  file: string,
  content: string
): Promise<CodeQualityResult> {
  const prompt = `${CODE_QUALITY_ANALYZER_PROMPT}

Analyze this file for code quality issues:

File: ${file}

\`\`\`
${content}
\`\`\`

IMPORTANT: You MUST respond with valid JSON matching this exact structure:
{
  "file": "${file}",
  "issues": [
    {
      "line": <number>,
      "severity": "critical" | "high" | "medium" | "low" | "info",
      "category": "security" | "performance" | "maintainability" | "style" | "bug-risk" | "best-practice",
      "description": "<description>",
      "suggestion": "<suggestion>"
    }
  ],
  "overallScore": <0-100>,
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

  // Extract JSON from the response (it might be wrapped in markdown code blocks)
  const jsonMatch = responseText.match(/```(?:json)?\n?([\s\S]*?)\n?```/) || [, responseText];
  const jsonText = jsonMatch[1] || responseText;

  try {
    const parsed = JSON.parse(jsonText.trim());
    return CodeQualityResultSchema.parse(parsed);
  } catch (error) {
    // Fallback: return minimal valid result
    return {
      file,
      issues: [],
      overallScore: 70,
      summary: 'Analysis completed but failed to parse structured output'
    };
  }
}
