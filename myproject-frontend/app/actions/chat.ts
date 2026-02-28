'use server'

import { apiFetch } from "@/lib/api-client";
import { Agent } from "@/types/chat";

export async function getChatHistoryAction(sessionId: number) {
  const res = await apiFetch(`/chats/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function sendChatMessageAction(sessionId: number, userInput: string) {
  const params = new URLSearchParams({ user_input: userInput });
  const res = await apiFetch(`/chats/${sessionId}/message?${params.toString()}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}

export async function getAgentsAction(): Promise<Agent[]> {
  const res = await apiFetch(`/agents/`);
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}
