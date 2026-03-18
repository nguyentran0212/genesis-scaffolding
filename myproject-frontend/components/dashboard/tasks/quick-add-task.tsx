"use client";

import { useState } from "react";
import { Plus, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { createTaskAction, deleteTaskAction } from "@/app/actions/productivity";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface QuickAddTaskProps {
  defaultProjectId?: number;
  showToast?: boolean; // New prop
}

export function QuickAddTask({
  defaultProjectId,
  showToast = false
}: QuickAddTaskProps) {
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const taskTitle = title.trim();

    if (!taskTitle || loading) return;

    setLoading(true);
    try {
      const newTask = await createTaskAction({
        title: taskTitle,
        project_ids: defaultProjectId ? [defaultProjectId] : [],
        status: "todo",
      });

      // 1. Clear input immediately for snappy UX
      setTitle("");

      // 2. Trigger Success Toast
      if (showToast) {
        toast.success("Task created", {
          description: `"${taskTitle}" added successfully.`,
          action: {
            label: "Undo",
            onClick: async () => {
              await deleteTaskAction(newTask.id);
              router.refresh();
            }
          }
        });
      }

      router.refresh();
    } catch (error) {
      // 3. Trigger Error Toast
      if (showToast) {
        toast.error("Failed to create task", {
          description: "Please try again later.",
        });
      }
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative group w-full">
      {loading ? (
        <Loader2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-primary" />
      ) : (
        <Plus className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
      )}
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Add a new task..."
        className="pl-10 h-11 bg-transparent border-dashed focus:border-solid transition-all"
        disabled={loading}
        autoFocus
      />
    </form>
  );
}
