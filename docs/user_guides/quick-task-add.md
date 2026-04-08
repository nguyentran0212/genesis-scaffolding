# Quick Task Add

The Quick Task Add input lets you rapidly create tasks with natural language. It's accessible via the floating action menu (FAB) in the dashboard.

## Syntax Reference

| Pattern | Example | Result |
|---------|---------|--------|
| `#project-name` | `#Marketing` | Assigns task to a project |
| `due YYYY-MM-DD` | `due 2026-04-15` | Sets a hard deadline |
| `by <date>` | `by Friday` | Sets a hard deadline |
| `@ <date> at <time>` | `@ tomorrow at 2:30pm` | Creates a calendar appointment |
| `<date>` | `tomorrow`, `friday`, `apr 15` | Sets the assigned/planning date |

## Creating a Calendar Appointment

To create a task that appears as a time-blocked event on your calendar, use the `@` symbol followed by a date and time:

```
Meeting with Sarah @ tuesday at 2pm
Lunch reservation @ friday 12pm
Call mom @ tomorrow at 9am
```

The `@` keyword tells the parser to set `scheduledStart` instead of just an assigned date.

## Examples

**Simple task:**
```
Buy groceries
```

**Task with project:**
```
Write report #Marketing
```

**Task with deadline:**
```
Submit expenses due friday
```

**Calendar appointment:**
```
Team standup @ tomorrow at 10am
```

**Task with project and appointment:**
```
Client call #Acme @ monday at 3pm
```
