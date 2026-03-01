'use client';

import { ChatSession } from '@/types/chat';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageSquare, Calendar, ArrowRight, Bot } from 'lucide-react';
import { formatRelativeTime } from '@/lib/date-utils';
import Link from 'next/link';

interface ChatHistoryTableProps {
  sessions: ChatSession[];
}

export function ChatHistoryTable({ sessions }: ChatHistoryTableProps) {
  return (
    <div className="rounded-md border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Agent</TableHead>
            <TableHead>Chat Title</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Active</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                No chat history found. Start a new conversation with an agent!
              </TableCell>
            </TableRow>
          )}
          {sessions.map((session) => (
            <TableRow key={session.id}>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-muted-foreground" />
                  <Badge variant="secondary" className="font-mono text-xs">
                    {session.agent_id}
                  </Badge>
                </div>
              </TableCell>
              <TableCell className="font-medium">
                <Link
                  href={`/dashboard/chats/${session.id}`}
                  className="hover:underline hover:text-primary transition-colors flex items-center gap-2"
                >
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  {session.title}
                </Link>
              </TableCell>
              <TableCell>
                {session.is_running ? (
                  <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20 border-green-500/20">
                    Active
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-muted-foreground">
                    Idle
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatRelativeTime(session.updated_at)}
                </div>
              </TableCell>
              <TableCell className="text-right">
                <Button asChild variant="ghost" size="sm" className="gap-2">
                  <Link href={`/dashboard/chats/${session.id}`}>
                    Resume
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
