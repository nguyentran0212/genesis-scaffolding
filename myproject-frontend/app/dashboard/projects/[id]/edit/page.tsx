import { getProjectAction, updateProjectAction, deleteProjectAction } from "@/app/actions/productivity";
import { PageContainer, PageBody } from "@/components/dashboard/page-container";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";


export default async function EditProjectPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params;

  const project = await getProjectAction(id);

  async function handleUpdate(formData: FormData) {
    "use server";
    await updateProjectAction(id, {
      name: formData.get("name"),
      description: formData.get("description"),
      deadline: formData.get("deadline") || null,
      status: formData.get("status"),
    });
    redirect(`/dashboard/projects/${id}`);
  }

  async function handleDelete() {
    "use server";
    await deleteProjectAction(id);
    redirect("/dashboard/projects");
  }

  return (
    <PageContainer variant="prose">
      <PageBody>
        <h1 className="text-2xl font-bold mb-6">Edit Project</h1>
        <form action={handleUpdate} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Project Name</Label>
            <Input id="name" name="name" defaultValue={project.name} required />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" name="description" defaultValue={project.description || ""} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                name="status"
                defaultValue={project.status}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="backlog">Backlog</option>
                <option value="todo">Todo</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="canceled">Canceled</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="deadline">Deadline</Label>
              <Input id="deadline" name="deadline" type="date" defaultValue={project.deadline?.split('T')[0] || ""} />
            </div>
          </div>

          <div className="flex gap-4 justify-between pt-4">
            <form action={handleDelete}>
              <Button variant="destructive" type="submit">Delete Project</Button>
            </form>
            <div className="flex gap-2">
              <Button variant="ghost" type="button">Cancel</Button>
              <Button type="submit">Save Changes</Button>
            </div>
          </div>
        </form>
      </PageBody>
    </PageContainer>
  );
}
