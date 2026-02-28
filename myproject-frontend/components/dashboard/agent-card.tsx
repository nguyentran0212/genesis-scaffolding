import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bot, Wrench, Users } from 'lucide-react';
import { Agent } from '@/types/chat';
import { StartChatButton } from './start-chat-button';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const modelDisplay = agent.model_name || 'Default Model';
  return (
    <Card className="flex flex-col hover:shadow-md transition-all duration-200 border-slate-200">
      <CardHeader>
        <div className="flex justify-between items-start mb-2">
          <Badge
            variant="secondary"
            className="text-[10px] font-mono uppercase tracking-wider max-w-[150px] truncate block"
            title={modelDisplay} // Shows full name on hover
          >
            {modelDisplay}
          </Badge>
          <Bot className="h-4 w-4 text-primary/50 shrink-0" />
        </div>
        <CardTitle className="text-xl font-bold line-clamp-1">
          {agent.name}
        </CardTitle>
        <CardDescription className="line-clamp-2 min-h-[40px]">
          {agent.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1">
        <div className="space-y-3">
          <div className="flex items-center text-sm text-muted-foreground">
            <Wrench className="mr-2 h-4 w-4" />
            <span>{agent.allowed_tools.length} Tools Available</span>
          </div>
          <div className="flex items-center text-sm text-muted-foreground">
            <Users className="mr-2 h-4 w-4" />
            <span>{agent.allowed_agents.length} Collaborators</span>
          </div>

          <div className="flex flex-wrap gap-1 pt-2">
            {agent.interactive && (
              <Badge variant="outline" className="text-[10px] bg-green-50 text-green-700 border-green-200">
                Interactive
              </Badge>
            )}
          </div>
        </div>
      </CardContent>

      <CardFooter className="border-t bg-slate-50/50 p-4">
        <StartChatButton agentId={agent.id} agentName={agent.name} />
      </CardFooter>
    </Card>
  );
}
