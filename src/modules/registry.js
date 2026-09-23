import { lazy } from "react";
import {
  Activity,
  BarChart3,
  HeartPulse,
  LayoutDashboard,
  Package,
  Puzzle,
  Share2,
  Sparkles,
  Users,
  Dumbbell,
} from "lucide-react";

/** UI module registry — add a module here to plug it into coach/admin nav. */
export const MODULE_REGISTRY = [
  {
    id: "coach-insights",
    name: "Coach Learning",
    description: "Taste priors from keep/replace decisions.",
    category: "coach",
    scope: "coach",
    icon: Sparkles,
    path: "/coach/insights",
    component: lazy(() =>
      import("../components/CoachInsights").then((m) => ({ default: m.CoachInsights })),
    ),
  },
  {
    id: "fms-assessment",
    name: "FMS Assessment",
    description: "Seven-screen movement screen.",
    category: "coach",
    scope: "coach",
    icon: Activity,
    path: null,
    embedded: true,
  },
  {
    id: "program-editor",
    name: "Program Editor",
    description: "Calendar week editor and approvals.",
    category: "coach",
    scope: "coach",
    icon: LayoutDashboard,
    path: null,
    embedded: true,
  },
  {
    id: "athlete-share",
    name: "Athlete Share",
    description: "Public read-only program links.",
    category: "coach",
    scope: "coach",
    icon: Share2,
    path: null,
    embedded: true,
  },
  {
    id: "lift-max-log",
    name: "1RM History",
    description: "Strength log on student profile.",
    category: "coach",
    scope: "coach",
    icon: Dumbbell,
    path: null,
    embedded: true,
  },
  {
    id: "analytics",
    name: "Analytics",
    description: "FMS trends and progression charts.",
    category: "platform",
    scope: "coach",
    icon: BarChart3,
    path: "/coach/analytics",
    component: lazy(() =>
      import("../components/modules/AnalyticsModule").then((m) => ({ default: m.AnalyticsModule })),
    ),
    badge: "Beta",
  },
  {
    id: "admin-dashboard",
    name: "Overview",
    description: "Platform stats and health summary.",
    category: "admin",
    scope: "admin",
    icon: LayoutDashboard,
    path: "/admin",
    adminOnly: true,
    component: lazy(() =>
      import("../components/admin/AdminDashboard").then((m) => ({ default: m.AdminDashboard })),
    ),
  },
  {
    id: "module-manager",
    name: "Modules",
    description: "Enable features plug-and-play.",
    category: "admin",
    scope: "admin",
    icon: Puzzle,
    path: "/admin/modules",
    adminOnly: true,
    component: lazy(() =>
      import("../components/admin/ModuleManager").then((m) => ({ default: m.ModuleManager })),
    ),
  },
  {
    id: "system-health",
    name: "System Health",
    description: "API, database, and integrations.",
    category: "admin",
    scope: "admin",
    icon: HeartPulse,
    path: "/admin/health",
    adminOnly: true,
    component: lazy(() =>
      import("../components/admin/SystemHealth").then((m) => ({ default: m.SystemHealth })),
    ),
  },
  {
    id: "coach-roster-admin",
    name: "Coaches",
    description: "All coaches and admin roles.",
    category: "admin",
    scope: "admin",
    icon: Users,
    path: "/admin/coaches",
    adminOnly: true,
    component: lazy(() =>
      import("../components/admin/CoachRoster").then((m) => ({ default: m.CoachRoster })),
    ),
  },
  {
    id: "recovery-programming",
    name: "Recovery Programming",
    description: "Programmed recovery sessions.",
    category: "platform",
    scope: "coach",
    icon: Package,
    path: null,
    embedded: true,
    badge: "Soon",
  },
];

export const REGISTRY_BY_ID = Object.fromEntries(MODULE_REGISTRY.map((m) => [m.id, m]));

export function navigableModules(modules, { admin = false } = {}) {
  return modules.filter((m) => {
    if (!m.enabled) return false;
    if (m.embedded || !m.path) return false;
    if (m.adminOnly && !admin) return false;
    if (m.scope === "admin" && !admin) return false;
    return true;
  });
}
