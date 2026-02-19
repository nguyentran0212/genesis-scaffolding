import { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { getCurrentUser } from '@/app/actions/auth';
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger
} from '@/components/ui/sidebar';
import {
  LayoutDashboard,
  Settings,
  Box,
  History,
  FileCode,
  AlarmClock
} from 'lucide-react';
import LogoutButton from '@/components/auth/logout-button';
import Link from 'next/link';
import DynamicHeader from '@/components/dashboard/dynamic-header';

const navItems = [
  { title: "Workflow Catalog", url: "/dashboard/workflows", icon: LayoutDashboard },
  { title: "Job History", url: "/dashboard/jobs", icon: History },
  { title: "Schedules", url: "/dashboard/schedules", icon: AlarmClock },
  { title: "Sandbox", url: "/dashboard/sandbox", icon: Box },
];

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();

  if (!user) {
    redirect('/login');
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar collapsible="icon">
          <SidebarHeader className="border-b px-4 py-2">
            <Link href="/dashboard/">
              <div className="flex items-center gap-2 font-semibold">
                <FileCode className="h-6 w-6" />
                <span className="group-data-[collapsible=icon]:hidden uppercase font-black tracking-tighter text-xl text-slate-900 dark:text-white">myproject</span>
              </div>
            </Link>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Application</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild tooltip={item.title}>
                        <Link href={item.url}>
                          <item.icon className="h-4 w-4" />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="border-t p-4">
            <div className="flex flex-col gap-4 group-data-[collapsible=icon]:items-center">
              <div className="flex flex-col group-data-[collapsible=icon]:hidden">
                <p className="text-xs font-medium text-muted-foreground">User</p>
                <p className="text-sm truncate font-bold">{user.username}</p>
              </div>
              <LogoutButton />
            </div>
          </SidebarFooter>
        </Sidebar>

        {/* Main Content Area */}
        <div className="flex flex-1 flex-col">
          <header className="flex h-16 items-center border-b px-6">
            <SidebarTrigger />
            <div className="h-6 w-[1px] bg-slate-200 dark:bg-slate-800" /> {/* Vertical Divider */}
            <div className="m-3 flex-1">
              <DynamicHeader />
            </div>
          </header>

          <main className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
