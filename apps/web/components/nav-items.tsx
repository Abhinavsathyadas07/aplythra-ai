import type { ReactNode } from "react";

const icon = (d: string): ReactNode => (
  <svg
    viewBox="0 0 24 24"
    width="22"
    height="22"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d={d} />
  </svg>
);

export type NavItem = { href: string; label: string; icon: ReactNode };

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: icon("M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10") },
  {
    href: "/jobs",
    label: "Jobs",
    icon: icon("M3 8h18v12H3zM8 8V5a1 1 0 011-1h6a1 1 0 011 1v3M3 13h18"),
  },
  {
    href: "/applications",
    label: "Applications",
    icon: icon("M9 4h6a1 1 0 011 1v1H8V5a1 1 0 011-1zM6 6h12v15H6zM9 11h6M9 15h6"),
  },
  {
    href: "/activity",
    label: "Activity",
    icon: icon("M3 12h4l3-8 4 16 3-8h4"),
  },
  {
    href: "/settings",
    label: "Settings",
    icon: icon("M4 6h10M18 6h2M4 12h2M10 12h10M4 18h12M20 18h0M14 4v4M8 10v4M18 16v4"),
  },
];
