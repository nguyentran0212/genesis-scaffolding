"use client";

import { useState } from "react";
import { Task } from "@/types/productivity";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { updateTaskAction } from "@/app/actions/productivity";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

export function TaskList({ tasks, defaultProjectId }: { tasks: Task[], defaultProjectId?: number }) {
  const router = useRouter();

  // Track which task is currently being updated to prevent double-clicks
  const [isProcessing, setIsProcessing] = useState<number | null>(null);

  async function toggleStatus(task: Task) {
    setIsProcessing(task.id);
    const isCompleting = task.status !== 'completed';
    const newStatus = isCompleting ? 'completed' : 'todo';

    try {
      await updateTaskAction(task.id, { status: newStatus });

      // Sonner Toast with Undo Action
      toast(isCompleting ? "Task completed" : "Task reopened", {
        description: `"${task.title}" has been updated.`,
        action: {
          label: "Undo",
          onClick: () => toggleStatus({ ...task, status: newStatus }),
        },
      });

      router.refresh();
    } catch (error) {
      toast.error("Failed to update task.");
    } finally {
      setIsProcessing(null);
    }
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 border rounded-lg border-dashed bg-muted/20">
        <p className="text-muted-foreground">No open tasks in this view.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-md overflow-hidden bg-card">
      <div className="divide-y">
        <AnimatePresence initial={false}>
          {tasks.map((task) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 1, height: "auto" }}
              exit={{
                opacity: 0,
                x: 30,
                height: 0,
                transition: { duration: 0.25, ease: "easeInOut" }
              }}
              className="flex items-center p-4 gap-4 group hover:bg-accent/50 transition-colors bg-card relative overflow-hidden"
            >
              <Checkbox
                disabled={isProcessing === task.id}
                checked={task.status === 'completed'}
                onCheckedChange={() => toggleStatus(task)}
              />

              <div className="flex-1 min-w-0">
                <p className={`font-medium transition-all duration-300 ${task.status === 'completed' ? 'line-through text-muted-foreground italic' : ''
                  }`}>
                  {task.title}
                </p>
                {task.assigned_date && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Scheduled: {task.assigned_date}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {task.status === 'completed' && (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 animate-in zoom-in duration-300" />
                )}
                <Badge
                  variant="outline"
                  className="opacity-0 group-hover:opacity-100 transition-opacity capitalize hidden sm:inline-flex"
                >
                  {task.status.replace('_', ' ')}
                </Badge>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
