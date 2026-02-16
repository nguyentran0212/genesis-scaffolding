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
  FileCode
} from 'lucide-react';
import LogoutButton from '@/components/auth/logout-button';
import Link from 'next/link';

const navItems = [
  { title: "Workflow Catalog", url: "/dashboard", icon: LayoutDashboard },
  { title: "Job History", url: "/dashboard/jobs", icon: History },
  { title: "Sandbox", url: "/dashboard/sandbox", icon: Box },
];

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();

  if (!user) {
    redirect('/login');
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        {/* Navigation Sidebar */}
        <Sidebar collapsible="icon">
          <SidebarHeader className="border-b px-4 py-2">
            <div className="flex items-center gap-2 font-semibold">
              <FileCode className="h-6 w-6" />
              <span className="group-data-[collapsible=icon]:hidden">Workflow Engine</span>
            </div>
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
            <div className="ml-4 flex-1">
              <h2 className="text-lg font-semibold tracking-tight">System</h2>
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
