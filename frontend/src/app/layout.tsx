import "../styles/globals.css";
import "../styles/workflow.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "KHAGATARA", description: "Amazon listing automation" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
