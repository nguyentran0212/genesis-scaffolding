import { AlertCircle, CheckCircle2, Clock, Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { JobStatus } from "@/types/job";

export function JobStatusBanner({ status, error }: { status: JobStatus, error?: string | null }) {
  const configs = {
    pending: { icon: Clock, color: "bg-slate-100 text-slate-600", label: "Pending" },
    running: { icon: Loader2, color: "bg-blue-100 text-blue-600", label: "Running" },
    completed: { icon: CheckCircle2, color: "bg-green-100 text-green-700", label: "Completed" },
    failed: { icon: AlertCircle, color: "bg-red-100 text-red-700", label: "Failed" },
  };

  const config = configs[status];
  const Icon = config.icon;

  return (
    <div className="space-y-4">
      <div className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${config.color}`}>
        <Icon className={`h-5 w-5 ${status === 'running' ? 'animate-spin' : ''}`} />
        <span className="font-semibold">{config.label}</span>
      </div>

      {status === 'failed' && error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error Detail</AlertTitle>
          <AlertDescription className="font-mono text-xs mt-2 bg-red-50 p-2 rounded border border-red-200">
            {error}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
