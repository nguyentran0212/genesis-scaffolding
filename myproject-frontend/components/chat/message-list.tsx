'use client'
import React, { useEffect, useRef, memo } from 'react';
import { MessageBubble } from './message-bubble';
import { ChatMessage } from '@/types/chat';

export const MessageList = memo(({ messages }: { messages: ChatMessage[] }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const userScrolledUpRef = useRef(false);
  const lastMessageCountRef = useRef(messages.length);

  // Detect if user manually scrolled up (away from bottom)
  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;

    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    // If user scrolled up more than 50px from bottom, mark as scrolled up
    userScrolledUpRef.current = distanceFromBottom > 50;
  };

  // Reset scroll flag when a new user message arrives (new turn)
  useEffect(() => {
    const currentCount = messages.length;
    const prevCount = lastMessageCountRef.current;

    // New message added (user message starts a new turn)
    if (currentCount > prevCount) {
      const lastMessage = messages[messages.length - 1];
      // If the new message is from user, this is a new turn - reset auto-scroll
      if (lastMessage?.role === 'user') {
        userScrolledUpRef.current = false;
      }
    }

    lastMessageCountRef.current = currentCount;
  }, [messages]);

  useEffect(() => {
    if (userScrolledUpRef.current) return;

    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 min-h-0 overflow-y-auto w-full"
    >
      {/* Content wrapper */}
      <div className="chat-viewport-container py-4 space-y-6">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        {/* Invisible div for scroll anchoring */}
        <div ref={scrollRef} className="h-4 w-full shrink-0" />
      </div>

    </div>
  );
});
