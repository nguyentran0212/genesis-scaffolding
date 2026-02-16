import { z } from 'zod';
import { WorkflowManifest } from '@/types/workflow';

// Define the return type as a ZodObject with any shape
export function generateZodSchema(workflow: WorkflowManifest): z.ZodObject<any> {
  const shape: Record<string, z.ZodTypeAny> = {};

  Object.entries(workflow.inputs).forEach(([key, config]) => {
    let validator: z.ZodTypeAny;

    switch (config.type) {
      case 'int':
      case 'float':
        validator = z.coerce.number();
        break;
      case 'bool':
        validator = z.boolean();
        break;
      case 'list[string]':
        validator = z.array(z.string());
        break;
      default:
        validator = z.string();
    }

    if (config.required) {
      // Use refined validation for required fields
      if (config.type === 'string') {
        validator = (validator as z.ZodString).min(1, `${key} is required`);
      }
    } else {
      validator = validator.optional().or(z.literal(''));
    }

    shape[key] = validator;
  });

  return z.object(shape);
}
