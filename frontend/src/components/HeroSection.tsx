import { Shield } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="py-12 px-4 text-center">
      <div className="max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
          <Shield className="w-4 h-4" />
          <span className="text-sm font-medium">Apart Research Hackathon Project</span>
        </div>
        
        <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-br from-foreground to-muted-foreground bg-clip-text text-transparent">
          Bot Detector
        </h1>
        
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Detect if a Bluesky account is likely a bot
        </p>
      </div>
    </section>
  );
};

export default HeroSection;
