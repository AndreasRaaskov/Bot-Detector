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
    // TODO: Call backend API and update results
    // For now, results remain as null (NaN)
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
