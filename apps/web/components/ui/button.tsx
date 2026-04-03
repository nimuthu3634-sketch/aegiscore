import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-[18px] border text-sm font-semibold tracking-[0.01em] transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "border-[#f68c3f] bg-[linear-gradient(135deg,#ff8a36_0%,#ff7a1a_55%,#dc6310_100%)] px-4 py-2 text-white shadow-[0_18px_34px_rgba(255,122,26,0.24)] hover:-translate-y-[1px] hover:shadow-[0_22px_38px_rgba(255,122,26,0.28)]",
        outline:
          "border-black/10 bg-white/80 px-4 py-2 text-[var(--foreground)] shadow-[0_10px_24px_rgba(17,17,17,0.05)] hover:border-[#ffb37f] hover:bg-white",
        ghost: "border-transparent px-3 py-2 text-[var(--muted)] hover:bg-white/70 hover:text-[var(--foreground)]",
        subtle: "border-[#ffd9bf] bg-[var(--accent-soft)] px-4 py-2 text-[#9c4a0c] hover:bg-[#ffe4cf]",
        danger: "border-[#1f1a16] bg-[#111111] px-4 py-2 text-white shadow-[0_18px_34px_rgba(17,17,17,0.22)] hover:bg-[#201c19]",
      },
      size: {
        sm: "h-9 px-3.5 text-xs",
        default: "h-11 px-4.5",
        lg: "h-12 px-6",
        icon: "h-11 w-11",
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
