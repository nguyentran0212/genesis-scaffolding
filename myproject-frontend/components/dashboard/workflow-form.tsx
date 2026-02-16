'use client';

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
import { Rocket } from 'lucide-react';

export function WorkflowForm({ workflow }: { workflow: WorkflowManifest }) {
  const schema = generateZodSchema(workflow);

  const form = useForm({
    // @ts-ignore - The schema is generated dynamically at runtime, 
    // which confuses the static analysis of the zodResolver type definition.
    resolver: zodResolver(schema),
    defaultValues: Object.fromEntries(
      Object.entries(workflow.inputs).map(([key, val]) => [key, val.default ?? ''])
    ),
  });

  async function onSubmit(values: any) {
    console.log('Submitting to /jobs:', values);
    // TODO: Implement job submission action
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
                  {/* For now, we use a simple Input. 
                      Next we will implement the Switch and the Sandbox Picker */}
                  <Input
                    placeholder={config.description}
                    {...field}
                    value={field.value ?? ''}
                  />
                </FormControl>
                <FormDescription>{config.description}</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        ))}

        <Button type="submit" size="lg" className="w-full md:w-auto">
          <Rocket className="mr-2 h-4 w-4" /> Execute Workflow
        </Button>
      </form>
    </Form>
  );
}
