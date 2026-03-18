"use client";

import React, { useState } from "react";
import { Plus, X, ListTodo, Search, Calendar, MessageSquare, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { QuickAddTask } from "@/components/dashboard/tasks/quick-add-task";

type Position = "bottom-right" | "bottom-left" | "top-right" | "top-left";

interface FloatingActionMenuProps {
  position?: Position;
  defaultProjectId?: number;
}

export function FloatingActionMenu({
  position = "bottom-right",
  defaultProjectId
}: FloatingActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeWidget, setActiveWidget] = useState<"none" | "task">("none");

  // Position logic mapping
  const positionClasses: Record<Position, string> = {
    "bottom-right": "bottom-6 right-6 flex-col-reverse",
    "bottom-left": "bottom-6 left-6 flex-col-reverse items-start",
    "top-right": "top-20 right-6 flex-col",
    "top-left": "top-20 left-6 flex-col items-start",
  };

  const toggleMenu = () => {
    setIsOpen(!isOpen);
    setActiveWidget("none");
  };

  return (
    <div className={cn("fixed z-50 flex gap-3 items-center", positionClasses[position])}>

      {/* 1. MAIN TRIGGER BUTTON */}
      <Button
        size="icon"
        onClick={toggleMenu}
        className={cn(
          "h-14 w-14 rounded-full shadow-2xl transition-transform duration-300",
          isOpen ? "rotate-45 bg-destructive hover:bg-destructive/90" : "bg-primary"
        )}
      >
        <Zap className="h-6 w-6" />
      </Button>

      {/* 2. THE TRAY (Icons or Widget) */}
      {isOpen && (
        <div className="animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-200">
          {activeWidget === "task" ? (
            // TASK INPUT MODE
            <div className="bg-background border rounded-2xl shadow-2xl p-2 w-[300px] md:w-[400px] flex items-center gap-2">
              <div className="flex-1">
                <QuickAddTask defaultProjectId={defaultProjectId} showToast={true} />
              </div>
              <Button variant="ghost" size="icon" onClick={() => setActiveWidget("none")}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            // ICON TRAY MODE
            <div className="flex gap-2 bg-background/80 backdrop-blur-md border p-2 rounded-full shadow-xl">
              <TrayIcon
                icon={<ListTodo className="h-5 w-5" />}
                label="Add Task"
                onClick={() => setActiveWidget("task")}
                variant="primary"
              />
              {/* <TrayIcon icon={<MessageSquare className="h-5 w-5" />} label="Notes" onClick={() => { }} /> */}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TrayIcon({
  icon,
  onClick,
  variant = "ghost"
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: "ghost" | "primary"
}) {
  return (
    <Button
      variant={variant === "primary" ? "default" : "ghost"}
      size="icon"
      className="h-10 w-10 rounded-full"
      onClick={onClick}
    >
      {icon}
    </Button>
  );
}
