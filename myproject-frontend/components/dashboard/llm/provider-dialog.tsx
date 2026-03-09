"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { saveProviderAction } from "@/app/actions/llm-config";
import { toast } from "sonner";
import { useEffect } from "react";

const providerSchema = z.object({
  nickname: z.string().min(1, "Nickname is required"),
  name: z.string().optional(),
  base_url: z.string().optional(),
  api_key: z.string().min(1, "API Key is required"),
});

export function ProviderDialog({ open, onOpenChange, editing }: any) {
  const form = useForm<z.infer<typeof providerSchema>>({
    resolver: zodResolver(providerSchema),
    defaultValues: { nickname: "", name: "openrouter", base_url: "https://openrouter.ai/api/v1", api_key: "" },
  });

  useEffect(() => {
    if (editing) form.reset({ nickname: editing.nickname, ...editing.data });
    else form.reset({ nickname: "", name: "openrouter", base_url: "https://openrouter.ai/api/v1", api_key: "" });
  }, [editing, form, open]);

  async function onSubmit(values: z.infer<typeof providerSchema>) {
    try {
      const { nickname, ...data } = values;
      await saveProviderAction(nickname, data);
      toast.success("Provider saved");
      onOpenChange(false);
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>{editing ? "Edit Provider" : "Add Provider"}</DialogTitle></DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField control={form.control} name="nickname" render={({ field }) => (
              <FormItem>
                <FormLabel>Nickname (Unique ID)</FormLabel>
                <FormControl><Input {...field} disabled={!!editing} placeholder="e.g. my-openai" /></FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <FormField control={form.control} name="base_url" render={({ field }) => (
              <FormItem>
                <FormLabel>Base URL</FormLabel>
                <FormControl><Input {...field} placeholder="https://..." /></FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <FormField control={form.control} name="api_key" render={({ field }) => (
              <FormItem>
                <FormLabel>API Key</FormLabel>
                <FormControl><Input {...field} type="password" /></FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <DialogFooter><Button type="submit">Save Provider</Button></DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
