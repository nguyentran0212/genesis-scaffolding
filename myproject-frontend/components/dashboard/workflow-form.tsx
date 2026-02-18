'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { generateZodSchema } from '@/lib/workflow-utils';
import { WorkflowManifest } from '@/types/workflow';
import { SandboxFile } from '@/types/sandbox';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Rocket, Loader2 } from 'lucide-react';
import { createJobAction } from '@/app/actions/job';
import { toast } from 'sonner';
import { SandboxFilePicker } from '@/components/dashboard/sandbox-file-picker';
import { SandboxMultiFilePicker } from '@/components/dashboard/sandbox-multi-file-picker';

// Heuristic function to guess whether a string input field requires input or textarea
const isLongTextField = (key: string) => {
  const longTextKeywords = ['prompt', 'description', 'instruction', 'content', 'text', 'query', 'body', 'markdown', 'summary'];
  return longTextKeywords.some(keyword => key.toLowerCase().includes(keyword));
};


export function WorkflowForm({ workflow }: { workflow: WorkflowManifest }) {
  const schema = generateZodSchema(workflow);
  const [isPending, setIsPending] = useState(false);

  const form = useForm({
    // @ts-ignore - The schema is generated dynamically at runtime, 
    // which confuses the static analysis of the zodResolver type definition.
    resolver: zodResolver(schema),
    defaultValues: Object.fromEntries(
      Object.entries(workflow.inputs).map(([key, val]) => {
        if (val.type === 'list[file]') return [key, []];
        if (val.type === 'file') return [key, null]; // Use null, not ''
        return [key, val.default ?? ''];
      })
    ),
  });

  async function onSubmit(values: any) {
    setIsPending(true);

    // Create a copy to modify
    const processedValues = { ...values };

    // Transform file lists from Objects back to Paths for the Backend
    for (const [key, config] of Object.entries(workflow.inputs)) {
      if (config.type === 'list[file]' && Array.isArray(processedValues[key])) {
        processedValues[key] = processedValues[key].map((f: SandboxFile) => f.relative_path);
      }
      if (config.type === 'file' && typeof processedValues[key] === 'object') {
        processedValues[key] = processedValues[key].relative_path;
      }
    }

    try {
      await createJobAction(workflow.id, processedValues);
      toast.success("Job submitted!");
    } catch (error: any) {
      toast.error(error.message);
      setIsPending(false);
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {Object.entries(workflow.inputs).map(([key, config]) => (
          <FormField
            key={key}
            control={form.control}
            name={key}
            render={({ field }) => (
              <FormItem className="bg-white p-4 rounded-lg border shadow-sm">
                <FormLabel className="text-base font-semibold capitalize">
                  {key.replace(/_/g, ' ')}
                </FormLabel>
                <FormControl>
                  {(() => {
                    switch (config.type) {
                      case 'file':
                        return (
                          <SandboxFilePicker
                            value={field.value} // Remove ?? ''
                            onChange={field.onChange}
                            placeholder={config.description}
                          />
                        );
                      case 'list[file]':
                        return (
                          <SandboxMultiFilePicker
                            value={field.value || []}
                            onChange={field.onChange}
                            placeholder={config.description}
                          />
                        );
                      case 'bool':
                        return (
                          <div className="flex items-center space-x-2 pt-2">
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                              disabled={isPending}
                            />
                            <span className="text-sm text-muted-foreground">Enable this option</span>
                          </div>
                        );
                      case 'int':
                      case 'float':
                        return (
                          <Input
                            type="number"
                            {...field}
                            disabled={isPending}
                            onChange={(e) => field.onChange(config.type === 'int' ? parseInt(e.target.value) : parseFloat(e.target.value))}
                          />
                        );
                      case 'string':
                      default:
                        if (isLongTextField(key)) {
                          return (
                            <Textarea
                              placeholder={config.description}
                              className="min-h-[120px] resize-y"
                              {...field}
                              disabled={isPending}
                              value={field.value ?? ''}
                            />
                          );
                        }
                        return (
                          <Input
                            placeholder={config.description}
                            {...field}
                            disabled={isPending}
                            value={field.value ?? ''}
                          />
                        );
                    }
                  })()}
                </FormControl>
                <FormDescription>{config.description}</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        ))}

        <Button
          type="submit"
          size="lg"
          className="w-full md:w-auto min-w-[150px]"
          disabled={isPending}
        >
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Dispatching...
            </>
          ) : (
            <>
              <Rocket className="mr-2 h-4 w-4" />
              Execute Workflow
            </>
          )}
        </Button>
      </form>
    </Form>
  );
}
