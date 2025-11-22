import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface ResultsSectionProps {
  handle: string | null;
  results: {
    followRatio: number | null;
    postingPattern: number | null;
    textAnalysis: number | null;
    llmDetection: number | null;
    overallScore: number | null;
  };
}

const ResultsSection = ({ handle, results }: ResultsSectionProps) => {
  const scoreColor = (score: number | null) => {
    if (score === null) return "text-muted-foreground";
    if (score < 30) return "text-green-600";
    if (score < 70) return "text-yellow-600";
    return "text-red-600";
  };

  const formatScore = (score: number | null) => {
    return score === null ? "NaN" : `${score.toFixed(1)}%`;
  };

  return (
    <section className="py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {handle && (
          <div className="mb-6 text-center">
            <p className="text-lg">
              Analyzing: <span className="font-semibold text-primary">@{handle}</span>
            </p>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          <Card className="p-6">
            <h3 className="font-semibold mb-2">Follow/Follower Ratio</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Analyzes the balance between follows and followers. Bots often have unusual ratios.
            </p>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">Score:</span>
              <span className={`text-2xl font-bold ${scoreColor(results.followRatio)}`}>
                {formatScore(results.followRatio)}
              </span>
            </div>
            {results.followRatio !== null && (
              <Progress value={results.followRatio} className="h-2" />
            )}
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-2">Posting Patterns</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Examines timing and frequency of posts. Bots often post at regular intervals.
            </p>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">Score:</span>
              <span className={`text-2xl font-bold ${scoreColor(results.postingPattern)}`}>
                {formatScore(results.postingPattern)}
              </span>
            </div>
            {results.postingPattern !== null && (
              <Progress value={results.postingPattern} className="h-2" />
            )}
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-2">Text Analysis</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Evaluates content quality and patterns. Bots often use repetitive or generic text.
            </p>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">Score:</span>
              <span className={`text-2xl font-bold ${scoreColor(results.textAnalysis)}`}>
                {formatScore(results.textAnalysis)}
              </span>
            </div>
            {results.textAnalysis !== null && (
              <Progress value={results.textAnalysis} className="h-2" />
            )}
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-2">LLM Detection</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Detects AI-generated content patterns. Identifies posts likely written by language models.
            </p>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">Score:</span>
              <span className={`text-2xl font-bold ${scoreColor(results.llmDetection)}`}>
                {formatScore(results.llmDetection)}
              </span>
            </div>
            {results.llmDetection !== null && (
              <Progress value={results.llmDetection} className="h-2" />
            )}
          </Card>
        </div>

        <Card className="p-8 mt-6 bg-card/50 border-2">
          <div className="text-center">
            <h3 className="text-xl font-semibold mb-2">Overall Bot Likelihood</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Weighted composite score combining all detection signals
            </p>
            <div className={`text-6xl font-bold mb-4 ${scoreColor(results.overallScore)}`}>
              {formatScore(results.overallScore)}
            </div>
            {results.overallScore !== null && (
              <Progress value={results.overallScore} className="h-3" />
            )}
          </div>
        </Card>
      </div>
    </section>
  );
};

export default ResultsSection;
