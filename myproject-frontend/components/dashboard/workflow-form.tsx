'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { generateZodSchema } from '@/lib/workflow-utils';
import { WorkflowManifest } from '@/types/workflow';
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
import { Rocket, Loader2 } from 'lucide-react';
import { createJobAction } from '@/app/actions/job';
import { toast } from 'sonner';

export function WorkflowForm({ workflow }: { workflow: WorkflowManifest }) {
  const schema = generateZodSchema(workflow);
  const [isPending, setIsPending] = useState(false);
  const form = useForm({
    // @ts-ignore - The schema is generated dynamically at runtime, 
    // which confuses the static analysis of the zodResolver type definition.
    resolver: zodResolver(schema),
    defaultValues: Object.fromEntries(
      Object.entries(workflow.inputs).map(([key, val]) => [key, val.default ?? ''])
    ),
  });

  async function onSubmit(values: any) {
    setIsPending(true);
    try {
      await createJobAction(workflow.id, values);
      toast.success("Job submitted successfully!");
    } catch (error: any) {
      toast.error(error.message || "Something went wrong");
      setIsPending(false); // Only reset if we didn't redirect
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
                  <Input
                    placeholder={config.description}
                    {...field}
                    disabled={isPending}
                    value={field.value ?? ''}
                  />
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
