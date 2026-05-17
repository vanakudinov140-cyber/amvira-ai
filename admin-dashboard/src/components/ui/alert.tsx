import { cn } from "@/lib/utils";

export function Alert({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "destructive" | "success";
}) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-md border px-4 py-3 text-sm",
        variant === "destructive" &&
          "border-destructive/50 bg-destructive/10 text-red-200",
        variant === "success" &&
          "border-success/50 bg-success/10 text-green-200",
        variant === "default" && "border-border bg-muted/50 text-foreground",
        className,
      )}
      {...props}
    />
  );
}
