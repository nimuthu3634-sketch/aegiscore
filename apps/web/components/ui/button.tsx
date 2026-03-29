import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-xl text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[var(--accent)] px-4 py-2 text-white hover:bg-[#e56c12]",
        outline: "border border-[var(--border)] bg-white px-4 py-2 text-[var(--foreground)] hover:border-[#d6d6d6]",
        ghost: "px-3 py-2 text-[var(--muted)] hover:bg-[#fff4eb] hover:text-[var(--foreground)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({ className, variant, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant }), className)} {...props} />;
}
