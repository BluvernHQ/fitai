import { cn } from "../lib/utils";

export function BrandMark({ size = "md", className }) {
  const sizes = {
    sm: "text-base",
    md: "text-lg md:text-xl",
    lg: "text-4xl sm:text-5xl md:text-6xl",
    xl: "text-5xl sm:text-6xl md:text-7xl",
  };
  return (
    <span className={cn("brand-font font-bold tracking-tighter text-white", sizes[size], className)}>
      FIT.AI <span className="text-lime-400">PRO</span>
    </span>
  );
}

export function PageShell({ children, size = "lg", className }) {
  return (
    <div
      className={cn(
        "page-shell",
        size === "sm" && "page-shell-sm",
        size === "md" && "page-shell-md",
        size === "lg" && "page-shell-lg",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PageHeader({ eyebrow, title, accent, description, actions, className }) {
  return (
    <header
      className={cn(
        "mb-6 md:mb-10 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between border-b border-white/[0.06] pb-6",
        className,
      )}
    >
      <div className="min-w-0">
        {eyebrow && <span className="eyebrow mb-2">{eyebrow}</span>}
        <h1 className="display-title text-3xl md:text-5xl text-white">
          {title}
          {accent != null && <span className="text-zinc-500"> {accent}</span>}
        </h1>
        {description && (
          <p className="mt-2 text-sm md:text-base text-zinc-400 max-w-xl leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3 shrink-0">{actions}</div>}
    </header>
  );
}

export function Surface({ children, interactive = false, className, as: Comp = "div", ...props }) {
  return (
    <Comp className={cn(interactive ? "surface-interactive" : "surface", className)} {...props}>
      {children}
    </Comp>
  );
}

export function FieldShell({ children, className }) {
  return <div className={cn("field-shell", className)}>{children}</div>;
}

export function Button({
  children,
  variant = "primary",
  className,
  type = "button",
  ...props
}) {
  const variants = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "btn-ghost",
  };
  return (
    <button type={type} className={cn(variants[variant], className)} {...props}>
      {children}
    </button>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="text-center py-14 md:py-20 px-6 surface border-dashed border-white/10">
      {Icon && <Icon className="w-11 h-11 text-zinc-600 mx-auto mb-4" strokeWidth={1.5} />}
      <h3 className="text-xl font-display font-medium text-zinc-300 mb-2">{title}</h3>
      {description && (
        <p className="text-zinc-500 max-w-sm mx-auto mb-6 text-sm leading-relaxed">{description}</p>
      )}
      {action}
    </div>
  );
}

export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-20 min-h-[45vh] gap-4">
      <div className="relative h-10 w-10">
        <span className="absolute inset-0 rounded-full border-2 border-white/10" />
        <span className="absolute inset-0 rounded-full border-2 border-transparent border-t-lime-400 animate-spin" />
      </div>
      <span className="eyebrow text-zinc-500">{label}</span>
    </div>
  );
}
