import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface BlueskyInputProps {
  onAnalyze: (handle: string) => void;
}

const BlueskyInput = ({ onAnalyze }: BlueskyInputProps) => {
  const [handle, setHandle] = useState("");
  const { toast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim()) {
      toast({
        title: "Handle required",
        description: "Please enter a Bluesky handle",
        variant: "destructive",
      });
      return;
    }
    
    const cleanHandle = handle.replace(/^@/, "");
    onAnalyze(cleanHandle);
    
    toast({
      title: "Analysis started",
      description: `Analyzing @${cleanHandle}...`,
    });
  };

  return (
    <section className="py-6 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-card border border-border rounded-lg p-6 shadow-lg">
          
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">@</span>
              <Input
                type="text"
                placeholder="username.bsky.social"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="pl-8"
              />
            </div>
            <Button type="submit" className="gap-2">
              <Search className="w-4 h-4" />
              Analyze
            </Button>
          </form>
        </div>
      </div>
    </section>
  );
};

export default BlueskyInput;
