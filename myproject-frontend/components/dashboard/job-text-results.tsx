import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { isPathResult, cleanPythonResult } from "@/lib/job-utils";

export function JobTextResults({ result }: { result: Record<string, string> | null }) {
  if (!result) return null;

  const textEntries = Object.entries(result).filter(
    ([key, value]) => !isPathResult(value) && !key.toLowerCase().includes('path')
  );

  if (textEntries.length === 0) return null;

  return (
    <div className="space-y-6">
      {textEntries.map(([key, value]) => (
        <Card key={key}>
          <CardHeader>
            <CardTitle className="text-sm font-medium capitalize">
              {key.replace(/_/g, ' ')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 bg-slate-50 p-4 rounded-md border">
              {cleanPythonResult(value)}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
