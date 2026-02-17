import { getJobByIdAction, getJobFilesAction } from "@/app/actions/job";
import { notFound } from "next/navigation";
import { JobStatusBanner } from "@/components/dashboard/job-status-banner";
import { JobParamsCard } from "@/components/dashboard/job-params-card";
import { JobTextResults } from "@/components/dashboard/job-text-results";
import { JobDownloads } from "@/components/dashboard/job-downloads";
import { Separator } from "@/components/ui/separator";
import { JobRealtimeListener } from "@/components/dashboard/job-realtime-listener";

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const jobId = parseInt(id);

  try {
    const [job, files] = await Promise.all([
      getJobByIdAction(jobId),
      getJobFilesAction(jobId)
    ]);

    return (
      <div className="max-w-6xl mx-auto space-y-8 pb-10">
        <JobRealtimeListener jobId={job.id} status={job.status} />
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight">Execution Detail</h1>
          <p className="text-muted-foreground font-mono text-sm">Job ID: #{job.id} • Workflow: {job.workflow_id}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar: Status & Config */}
          <div className="lg:col-span-1 space-y-6">
            <JobStatusBanner status={job.status} error={job.error_message} />
            <JobParamsCard inputs={job.inputs} />
          </div>

          {/* Main: Results & Downloads */}
          <div className="lg:col-span-2 space-y-8">
            <section>
              <h2 className="text-lg font-semibold mb-4">Results</h2>
              {job.status === 'completed' ? (
                <div className="space-y-6">
                  <JobTextResults result={job.result} />
                  <Separator />
                  <JobDownloads jobId={job.id} files={files} />
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center border-2 border-dashed rounded-xl text-muted-foreground">
                  Results will appear once the job is completed.
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    notFound();
  }
}
