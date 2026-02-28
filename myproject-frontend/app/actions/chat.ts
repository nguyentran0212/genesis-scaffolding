'use server'

import { apiFetch } from "@/lib/api-client";

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
