'use client'
import { useChat } from "./chat-context";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";

export function ChatWidget() {
  const { messages } = useChat();

  return (
    <>
      <MessageList messages={messages} />
      <ChatInput />
    </>
  );
}
