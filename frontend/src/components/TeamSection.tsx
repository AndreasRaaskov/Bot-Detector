import { Github, Mail, User } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface TeamMember {
  name: string;
  role: string;
  email?: string;
  github?: string;
}

const teamMembers: TeamMember[] = [
  {
    name: "Andreas Raaskov",
    role: "Technical Lead • MS.c Human-Centered AI",
    email: "Andreas@raaskov.dk",
    github: "https://github.com/AndreasRaaskov",
  },
  {
    name: "Mitali Mittal",
    role: "Technical • BA Computer Science",
    email: "mitalim@uci.edu",
    github: "https://github.com/mital-i",
  },
  {
    name: "Matt Pagett",
    role: "Policy",
    email: "Matt.pagett@gmail.com",
    github: "https://github.com/LemurTime",
  },
  {
    name: "Clara Bustamante",
    role: "Policy",
    email: "cbustamoreno@gmail.com",
  },
];

const TeamSection = () => {
  return (
    <section className="py-16 px-4 bg-accent/30">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-3">Our Team</h2>
          <p className="text-muted-foreground">
            A diverse team working across time zones to combat misinformation
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {teamMembers.map((member, index) => (
            <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex flex-col items-center text-center">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <User className="w-10 h-10 text-primary" />
                </div>
                
                <h3 className="font-semibold text-lg mb-1">{member.name}</h3>
                <p className="text-sm text-muted-foreground mb-4">{member.role}</p>
                
                <div className="flex gap-2">
                  {member.email && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      asChild
                    >
                      <a href={`mailto:${member.email}`} target="_blank" rel="noopener noreferrer">
                        <Mail className="w-4 h-4" />
                      </a>
                    </Button>
                  )}
                  {member.github && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      asChild
                    >
                      <a href={member.github} target="_blank" rel="noopener noreferrer">
                        <Github className="w-4 h-4" />
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground">
            <span className="font-medium">AI Team Members:</span> Claude (Backend) • Lovable (Frontend)
          </p>
        </div>
      </div>
    </section>
  );
};

export default TeamSection;
