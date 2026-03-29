import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-xl text-sm font-semibold transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[var(--accent)] px-4 py-2 text-white shadow-[0_10px_24px_rgba(255,122,26,0.18)] hover:bg-[#e56c12]",
        outline: "border border-[var(--border)] bg-white px-4 py-2 text-[var(--foreground)] hover:border-[#d6d6d6] hover:bg-[#fafafa]",
        ghost: "px-3 py-2 text-[var(--muted)] hover:bg-[#fff4eb] hover:text-[var(--foreground)]",
        subtle: "bg-[#fff4eb] px-4 py-2 text-[#9c4a0c] hover:bg-[#ffe6d1]",
        danger: "bg-[#111111] px-4 py-2 text-white hover:bg-[#2a2a2a]",
      },
      size: {
        sm: "h-9 px-3 text-xs",
        default: "h-10 px-4",
        lg: "h-11 px-5",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
