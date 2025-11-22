import { useState } from "react";
import HeroSection from "@/components/HeroSection";
import BlueskyInput from "@/components/BlueskyInput";
import ResultsSection from "@/components/ResultsSection";
import TeamSection from "@/components/TeamSection";

const Index = () => {
  const [analyzedHandle, setAnalyzedHandle] = useState<string | null>(null);
  const [results, setResults] = useState({
    followRatio: null,
    postingPattern: null,
    textAnalysis: null,
    llmDetection: null,
    overallScore: null,
  });

  const handleAnalyze = (handle: string) => {
    setAnalyzedHandle(handle);
    // Call backend API and update results
    // Use relative path so Vite dev proxy (configured in vite.config.ts) will forward to backend
    (async () => {
      try {
        const resp = await fetch(`/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ bluesky_handle: handle }),
        });

        if (!resp.ok) {
          console.error("API error", resp.statusText);
          return;
        }

        const data = await resp.json();
        console.log("API Response:", data); // Debug log

        // Map returned values into the local results shape if present
        // Convert scores from 0-1 scale to 0-100 percentage scale
        setResults((prev) => ({
          ...prev,
          followRatio: data.follow_analysis?.score ? data.follow_analysis.score * 100 : prev.followRatio,
          postingPattern: data.posting_pattern?.score ? data.posting_pattern.score * 100 : prev.postingPattern,
          textAnalysis: data.text_analysis?.score ? data.text_analysis.score * 100 : prev.textAnalysis,
          llmDetection: data.llm_analysis?.score ? data.llm_analysis.score * 100 : prev.llmDetection,
          overallScore: data.overall_score ? data.overall_score * 100 : prev.overallScore,
        }));
      } catch (err) {
        console.error("Failed to call analyze API", err);
      }
    })();
  };

  return (
    <div className="min-h-screen bg-background">
      <HeroSection />
      <BlueskyInput onAnalyze={handleAnalyze} />
      <ResultsSection handle={analyzedHandle} results={results} />
      <TeamSection />
      
      <footer className="py-8 px-4 border-t border-border">
        <div className="max-w-6xl mx-auto text-center text-sm text-muted-foreground">
          <p>
            A hackathon project for{" "}
            <a 
              href="https://apartresearch.com/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Apart Research
            </a>
            {" "}• MVP for detecting bot accounts on Bluesky
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
