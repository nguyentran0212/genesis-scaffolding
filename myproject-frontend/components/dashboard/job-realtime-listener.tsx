'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface JobRealtimeListenerProps {
  jobId: number;
  status: string; // Current status passed from the server component
}

export function JobRealtimeListener({ jobId, status }: JobRealtimeListenerProps) {
  const router = useRouter();

  useEffect(() => {
    // 1. Stop conditions: If job is already done, do not open connection.
    if (status === 'completed' || status === 'failed') {
      return;
    }

    // 2. Connect to the Proxy
    // The proxy will route this to FastAPI: /jobs/{id}/stream
    const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    // Helper to refresh Server Components
    const triggerUpdate = () => {
      router.refresh();
    };

    // 3. Listen for FastAPI specific events
    // Based on your WorkflowEventType enum

    eventSource.onopen = () => {
      console.log(`[SSE] Connected to job ${jobId}`);
    };

    // Standard updates
    eventSource.addEventListener("step_start", triggerUpdate);
    eventSource.addEventListener("step_completed", triggerUpdate);

    // Logs: Optional - if logs are frequent, you might debounce this 
    // or store logs in local state to avoid full page refreshes.
    eventSource.addEventListener("log", () => {
      // For now, let's refresh to show the log in the UI
      triggerUpdate();
    });

    eventSource.addEventListener("error", (e) => {
      console.error("Job Error:", (e as MessageEvent).data);
      triggerUpdate();
    });

    // 4. Handle Completion
    // Your python code sends { "event": "status", "data": "COMPLETED" } 
    // to signal the loop to break. We catch that here.
    eventSource.addEventListener("status", (e) => {
      const newStatus = (e as MessageEvent).data; // "COMPLETED" or "FAILED"
      if (newStatus === 'COMPLETED' || newStatus === 'FAILED') {
        eventSource.close();
        triggerUpdate(); // Final refresh to show download buttons
      }
    });

    // 5. Cleanup
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
