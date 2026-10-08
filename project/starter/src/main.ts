import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';
import { CodeReviewOrchestrator } from './orchestrator.js';
import { ReportGenerator } from './utils/report-generator.js';
import { logger } from './utils/logger.js';

// Load environment variables
dotenv.config();

/**
 * Main entry point for the Claude Multi-Agent Code Review System
 * Usage: npm run dev <owner> <repo> <pr-number>
 */
async function main() {
  const [owner, repo, prStr] = process.argv.slice(2);

  // Validate command line arguments
  if (!owner || !repo || !prStr) {
    console.error('❌ Error: Missing required arguments');
    console.error('\nUsage: npm run dev <owner> <repo> <pr-number>');
    console.error('Example: npm run dev facebook react 12345');
    process.exit(1);
  }

  // Convert prStr to number and validate it's a valid integer
  const prNumber = parseInt(prStr, 10);
  if (isNaN(prNumber) || prNumber <= 0) {
    console.error(`❌ Error: Invalid PR number "${prStr}". Must be a positive integer.`);
    process.exit(1);
  }

  // Validate authentication
  const hasAnthropicKey = !!process.env.ANTHROPIC_API_KEY;
  const hasAwsKeys = !!(process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY);

  if (!hasAnthropicKey && !hasAwsKeys) {
    console.error('❌ Error: No authentication configured');
    console.error('\nYou must configure ONE of the following:');
    console.error('  1. Anthropic API:');
    console.error('     export ANTHROPIC_API_KEY=sk-ant-your-key-here');
    console.error('  2. AWS Bedrock:');
    console.error('     export AWS_ACCESS_KEY_ID=your-key');
    console.error('     export AWS_SECRET_ACCESS_KEY=your-secret');
    console.error('     export AWS_REGION=us-east-1');
    process.exit(1);
  }

  // Log authentication method
  if (hasAwsKeys) {
    if (!process.env.AWS_REGION) {
      console.error('❌ Error: AWS_REGION is required when using AWS Bedrock authentication');
      process.exit(1);
    }
    console.log('🔐 Using AWS Bedrock authentication');
  } else {
    console.log('🔐 Using Anthropic API authentication');
  }

  // Validate ANTHROPIC_MODEL environment variable
  if (!process.env.ANTHROPIC_MODEL) {
    console.error('❌ Error: ANTHROPIC_MODEL environment variable is not set');
    console.error('\nSet it in your .env file:');
    console.error('  For Anthropic API: ANTHROPIC_MODEL=claude-sonnet-4-5-20250929');
    console.error('  For AWS Bedrock: ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0');
    process.exit(1);
  }

  console.log(`\n🤖 Model: ${process.env.ANTHROPIC_MODEL}`);
  console.log(`📋 Reviewing PR: ${owner}/${repo}#${prNumber}\n`);

  try {
    // Create orchestrator instance
    const orchestrator = new CodeReviewOrchestrator({
      rateLimits: {
        maxRequestsPerMinute: 50,
        maxTokensPerMinute: 100000,
        maxConcurrent: 5
      }
    });

    // Review the pull request
    console.log('🔍 Starting code review...\n');
    const report = await orchestrator.reviewPullRequest(owner, repo, prNumber);

    // Create reports directory if it doesn't exist
    const reportsDir = 'reports';
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    // Generate formatted reports
    const generator = new ReportGenerator();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const baseFilename = `${owner}-${repo}-${prNumber}-${timestamp}`;

    // Save Markdown report
    const markdownReport = generator.generateMarkdownReport(report);
    const markdownPath = path.join(reportsDir, `${baseFilename}.md`);
    fs.writeFileSync(markdownPath, markdownReport, 'utf-8');
    console.log(`✅ Markdown report saved: ${markdownPath}`);

    // Save HTML report
    const htmlReport = generator.generateHTMLReport(report);
    const htmlPath = path.join(reportsDir, `${baseFilename}.html`);
    fs.writeFileSync(htmlPath, htmlReport, 'utf-8');
    console.log(`✅ HTML report saved: ${htmlPath}`);

    // Save JSON report
    const jsonReport = generator.generateJSONReport(report);
    const jsonPath = path.join(reportsDir, `${baseFilename}.json`);
    fs.writeFileSync(jsonPath, jsonReport, 'utf-8');
    console.log(`✅ JSON report saved: ${jsonPath}`);

    // Print summary
    console.log(`\n📊 Review Summary:`);
    console.log(`   Overall Score: ${report.summary.overallScore}/100`);
    console.log(`   Files Reviewed: ${report.summary.totalFiles}`);
    console.log(`   Critical Issues: ${report.summary.criticalIssues}`);
    console.log(`   High Priority Tests: ${report.summary.highPriorityTests}`);
    console.log(`   Refactoring Opportunities: ${report.summary.refactoringOpportunities}`);
    console.log(`\n✨ Review complete! Duration: ${report.metadata.duration}ms\n`);

  } catch (error) {
    logger.error('Review failed', { error });
    console.error('\n❌ Error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();
