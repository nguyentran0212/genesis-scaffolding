export const dynamic = 'force-dynamic';
export const fetchCache = 'force-no-store';

import { getChatHistoryAction } from "@/app/actions/chat";
import { notFound } from "next/navigation";
import { ChatProvider } from "@/components/chat/chat-context";
import { ChatWidget } from "@/components/chat/chat-widget";

export default async function ChatDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const sessionId = parseInt(id);

  try {
    const data = await getChatHistoryAction(sessionId);
    const initialMessages = data.messages.map((m: any) => m.payload);

    return (
      <ChatProvider session={data.session} initialMessages={initialMessages}>
        <div className="max-w-4xl mx-auto h-[calc(100vh-120px)] flex flex-col pt-6 pb-2">
          <header className="mb-4 px-4">
            <h1 className="text-2xl font-bold tracking-tight">{data.session.title}</h1>
            <p className="text-muted-foreground text-sm">Session ID: #{data.session.id}</p>
          </header>

          <main className="flex-1 overflow-hidden flex flex-col">
            <ChatWidget />
          </main>
        </div>
      </ChatProvider>
    );
  } catch (error) {
    notFound();
  }
}
