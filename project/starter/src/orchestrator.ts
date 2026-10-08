import { ReviewReport } from './types/report-types.js';
import { RateLimiter, RateLimiterConfig, DEFAULT_RATE_LIMITS } from './utils/rate-limiter.js';
import { analyzeCodeQuality, analyzeTestCoverage, suggestRefactorings } from './agents/index.js';
import { logger, logReviewStart, logReviewComplete, logReviewError } from './utils/logger.js';
import { withRetry, ReviewError, ErrorCodes } from './utils/error-handler.js';

/**
 * Orchestrator configuration options
 */
export interface OrchestratorOptions {
  rateLimits?: Partial<RateLimiterConfig>;
}

interface PRFile {
  filename: string;
  content: string;
}

/**
 * Main Code Review Orchestrator
 * Coordinates subagents to analyze pull requests and generate comprehensive reports
 */
export class CodeReviewOrchestrator {
  private rateLimiter: RateLimiter;

  constructor(options: OrchestratorOptions = {}) {
    this.rateLimiter = new RateLimiter(options.rateLimits || DEFAULT_RATE_LIMITS);
  }

  /**
   * Review a pull request using parallel subagent analysis
   * @param owner - Repository owner
   * @param repo - Repository name
   * @param prNumber - Pull request number
   * @returns Complete review report
   */
  async reviewPullRequest(
    owner: string,
    repo: string,
    prNumber: number
  ): Promise<ReviewReport> {
    const startTime = Date.now();
    logReviewStart(owner, repo, prNumber);

    try {
      // Fetch PR files (mock implementation for now since we don't have GitHub MCP yet)
      const files = await this.fetchPRFiles(owner, repo, prNumber);

      if (files.length === 0) {
        throw new ReviewError(
          'No files found in pull request',
          ErrorCodes.FILE_NOT_FOUND,
          { owner, repo, prNumber }
        );
      }

      logger.info(`Found ${files.length} files to review`, { owner, repo, prNumber });

      // Analyze each file with all three subagents in parallel
      const fileReviews = await Promise.all(
        files.map(file => this.analyzeFile(file))
      );

      // Calculate summary metrics
      const summary = this.calculateSummary(fileReviews);

      // Generate top recommendations
      const recommendations = this.generateRecommendations(fileReviews);

      // Build final report
      const report: ReviewReport = {
        pullRequest: { owner, repo, number: prNumber },
        fileReviews,
        summary,
        recommendations,
        metadata: {
          analyzedAt: new Date().toISOString(),
          duration: Date.now() - startTime,
          agentVersions: {
            'code-quality-analyzer': '1.0.0',
            'test-coverage-analyzer': '1.0.0',
            'refactoring-suggester': '1.0.0'
          }
        }
      };

      logReviewComplete(owner, repo, prNumber, summary.overallScore, report.metadata.duration);
      return report;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      logReviewError(owner, repo, prNumber, err);
      throw error;
    }
  }

  /**
   * Analyze a single file with all three subagents in parallel
   */
  private async analyzeFile(file: PRFile) {
    logger.debug(`Analyzing file: ${file.filename}`);

    // Run all three analyses in parallel with rate limiting and retry logic
    const [codeQuality, testCoverage, refactorings] = await Promise.all([
      this.withRateLimitAndRetry(() => analyzeCodeQuality(file.filename, file.content)),
      this.withRateLimitAndRetry(() => analyzeTestCoverage(file.filename, file.content)),
      this.withRateLimitAndRetry(() => suggestRefactorings(file.filename, file.content))
    ]);

    return {
      file: file.filename,
      codeQuality,
      testCoverage,
      refactorings
    };
  }

  /**
   * Wrap an operation with rate limiting and retry logic
   */
  private async withRateLimitAndRetry<T>(fn: () => Promise<T>): Promise<T> {
    return withRetry(async () => {
      await this.rateLimiter.acquire(2000); // Estimate 2k tokens per request
      try {
        const result = await fn();
        this.rateLimiter.release(2000);
        return result;
      } catch (error) {
        this.rateLimiter.release(2000);
        throw error;
      }
    });
  }

  /**
   * Fetch PR files from GitHub
   * TODO: Implement actual GitHub MCP integration
   * For now, returns mock data for testing
   */
  private async fetchPRFiles(owner: string, repo: string, prNumber: number): Promise<PRFile[]> {
    // Mock implementation - in production this would use GitHub MCP
    logger.warn('Using mock PR files - GitHub MCP integration not yet implemented');

    return [
      {
        filename: 'src/payment.ts',
        content: `// Mock file content for testing
export class PaymentProcessor {
  async processPayment(amount: number, cardNumber: string) {
    if (amount <= 0) {
      throw new Error('Invalid amount');
    }
    // Process payment...
    return { success: true, transactionId: '12345' };
  }
}`
      }
    ];
  }

  /**
   * Calculate summary metrics from all file reviews
   */
  private calculateSummary(fileReviews: any[]) {
    const totalFiles = fileReviews.length;

    // Calculate average quality score
    const avgScore = fileReviews.reduce((sum, r) => sum + r.codeQuality.overallScore, 0) / totalFiles;

    // Count critical issues
    const criticalIssues = fileReviews.reduce((sum, r) =>
      sum + r.codeQuality.issues.filter((i: any) => i.severity === 'critical').length, 0
    );

    // Count high priority test gaps
    const highPriorityTests = fileReviews.reduce((sum, r) =>
      sum + r.testCoverage.untestedPaths.filter((p: any) => p.priority === 'high' || p.priority === 'critical').length, 0
    );

    // Count total refactoring opportunities
    const refactoringOpportunities = fileReviews.reduce((sum, r) =>
      sum + r.refactorings.suggestions.length, 0
    );

    return {
      totalFiles,
      overallScore: Math.round(avgScore),
      criticalIssues,
      highPriorityTests,
      refactoringOpportunities
    };
  }

  /**
   * Generate top recommendations from all file reviews
   */
  private generateRecommendations(fileReviews: any[]) {
    const recommendations: any[] = [];

    // Add critical security issues
    fileReviews.forEach(review => {
      review.codeQuality.issues
        .filter((i: any) => i.severity === 'critical' && i.category === 'security')
        .forEach((issue: any) => {
          recommendations.push({
            priority: 'critical' as const,
            category: 'Security',
            description: issue.description,
            files: [review.file]
          });
        });
    });

    // Add high priority test gaps
    fileReviews.forEach(review => {
      review.testCoverage.untestedPaths
        .filter((p: any) => p.priority === 'critical')
        .slice(0, 2)
        .forEach((path: any) => {
          recommendations.push({
            priority: 'high' as const,
            category: 'Testing',
            description: `Missing test: ${path.location}`,
            files: [review.file]
          });
        });
    });

    // Add high-impact refactorings
    fileReviews.forEach(review => {
      review.refactorings.suggestions
        .filter((s: any) => s.impact === 'high')
        .slice(0, 1)
        .forEach((suggestion: any) => {
          recommendations.push({
            priority: 'medium' as const,
            category: 'Refactoring',
            description: suggestion.description,
            files: [review.file]
          });
        });
    });

    // Sort by priority and limit to top 10
    const priorityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
    return recommendations
      .sort((a, b) => (priorityOrder[a.priority] || 999) - (priorityOrder[b.priority] || 999))
      .slice(0, 10);
  }
}
