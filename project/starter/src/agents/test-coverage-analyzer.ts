import { query } from '@anthropic-ai/claude-agent-sdk';
import { TEST_COVERAGE_ANALYZER_PROMPT } from '../prompts/index.js';
import { TestCoverageResultSchema, TestCoverageResult } from '../types/analysis-results.js';

const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5-20250929';

/**
 * Analyze a file for test coverage gaps
 * @param file - File path
 * @param content - File content
 * @returns Test coverage analysis result
 */
export async function analyzeTestCoverage(
  file: string,
  content: string
): Promise<TestCoverageResult> {
  const prompt = `${TEST_COVERAGE_ANALYZER_PROMPT}

Analyze this file for test coverage gaps:

File: ${file}

\`\`\`
${content}
\`\`\`

Think deeply about edge cases, error conditions, and untested branches.

IMPORTANT: You MUST respond with valid JSON matching this exact structure:
{
  "file": "${file}",
  "hasTests": <boolean>,
  "testFiles": ["<test file paths>"],
  "untestedPaths": [
    {
      "type": "function" | "class" | "branch" | "edge-case",
      "location": "<location>",
      "priority": "critical" | "high" | "medium" | "low",
      "reasoning": "<reasoning>",
      "suggestedTest": "<test case>"
    }
  ],
  "coverageEstimate": <0-100>,
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
    return TestCoverageResultSchema.parse(parsed);
  } catch (error) {
    // Fallback: return minimal valid result
    return {
      file,
      hasTests: false,
      testFiles: [],
      untestedPaths: [],
      coverageEstimate: 0,
      summary: 'Analysis completed but failed to parse structured output'
    };
  }
}
