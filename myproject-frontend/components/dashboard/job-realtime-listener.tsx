'use client';

import { useEffect, useRef, useTransition } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { forceRefreshAction } from '@/app/actions/refresh';

interface JobRealtimeListenerProps {
  jobId: number;
  status: string; // Current status passed from the server component
}

export function JobRealtimeListener({ jobId, status }: JobRealtimeListenerProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();
  const isTerminatingRef = useRef(false);

  useEffect(() => {
    // Helper to refresh Server Components
    // Add debounce to prevent "Step Completed" (Running) request from overwriting "Job Completed" (Done) request
    const triggerUpdate = async (isFinal = false) => {
      if (isTerminatingRef.current && !isFinal) return;

      // 1. Invalidate Server Cache via Action
      await forceRefreshAction(pathname);

      // 2. Trigger Client Refresh within a Transition
      // This tells React to prioritize this UI update
      startTransition(() => {
        router.refresh();
      });
    };

    // Stop conditions: If job is already done, do not open connection.
    // This is used when we open the job detail page and the job itself is already done or failed
    if (status === 'completed' || status === 'failed') {
      return;
    }

    // Connect to the Proxy
    // The proxy will route this to FastAPI: /jobs/{id}/stream
    const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    // Listen for FastAPI specific events
    // Based on WorkflowEventType enum defined in the core

    eventSource.onopen = () => {
      console.log(`[SSE] Connected to job ${jobId}`);
    };

    // Step updates
    // TODO: We will decide what to do with step related event later
    // eventSource.addEventListener("step_start", triggerUpdate);
    // eventSource.addEventListener("step_completed", triggerUpdate);

    // Logs: Optional 
    eventSource.addEventListener("log", () => {
      // For now, let's refresh to show the log in the UI
      triggerUpdate();
    });

    eventSource.addEventListener("error", (e) => {
      console.error("Job Error:", (e as MessageEvent).data);
      triggerUpdate();
    });

    // Handle Completion
    // Python code sends { "event": "status", "data": "COMPLETED" } 
    // to signal the loop to break. We catch that here.
    eventSource.addEventListener("status", (e) => {
      const newStatus = (e as MessageEvent).data;
      if (newStatus === 'COMPLETED' || newStatus === 'FAILED') {
        isTerminatingRef.current = true;
        eventSource.close();

        // Give the DB a final 500ms to settle then force the update
        setTimeout(() => {
          triggerUpdate(true);
        }, 500);
      }
    });

    // Cleanup
    eventSource.onerror = (err) => {
      console.error("SSE Error (closing connection):", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId, status, router]);

  return null; // This component is invisible
}
