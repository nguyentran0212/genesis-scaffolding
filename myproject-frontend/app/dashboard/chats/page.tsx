import { getAgentsAction } from '@/app/actions/chat';
import { AgentCard } from '@/components/dashboard/agent-card';

export default async function AgentsPage() {
  const allAgents = await getAgentsAction();

  // Filter to only show agents that are interactive
  const interactiveAgents = allAgents.filter((agent) => agent.interactive);

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Agent Registry
        </h1>
        <p className="text-lg text-muted-foreground">
          Select an agent to start a new specialized chat session.
        </p>
      </header>

      {interactiveAgents.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {interactiveAgents.map((agent) => (
            <AgentCard key={agent.name} agent={agent} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed rounded-xl bg-slate-50">
          <p className="text-muted-foreground font-medium">No agents found</p>
          <p className="text-sm text-muted-foreground/70">
            Make sure your AgentRegistry is populated in the backend.
          </p>
        </div>
      )}
    </div>
  );
}
