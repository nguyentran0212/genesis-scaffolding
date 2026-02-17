import { z } from 'zod';
import { WorkflowManifest } from '@/types/workflow';

export function generateZodSchema(workflow: WorkflowManifest) {
  const schemaFields: Record<string, any> = {};

  for (const [key, config] of Object.entries(workflow.inputs)) {
    let validator;

    switch (config.type) {
      case 'list[file]':
        // Allow an array of any (SandboxFile objects)
        validator = z.array(z.any());
        break;

      case 'file':
        // Allow an object (SandboxFile) or null
        validator = z.any().nullable();
        break;

      case 'list[string]':
        validator = z.array(z.string());
        break;

      case 'bool':
        validator = z.boolean().default(false);
        break;

      case 'string':
      default:
        validator = z.string();
        if (config.required) {
          validator = validator.min(1, `${key} is required`);
        } else {
          validator = validator.optional().or(z.literal(""));
        }
        break;
    }

    schemaFields[key] = validator;
  }

  return z.object(schemaFields);
}
