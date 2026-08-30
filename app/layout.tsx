import type { Metadata } from "next";
import "./globals.css";
import "./party-visual-language.css";
import "./analyst-evidence.css";
import "./evidence-freshness-status.css";
import "./poll-review-dossier.css";
import { PartyVisualKey } from "./party-visual-key";
import { AnalystEvidenceGuide } from "./analyst-evidence-guide";
import { EvidenceFreshnessStatus } from "./evidence-freshness-status";

export const metadata: Metadata = {
  title: "Victorian Election Forecast 2026",
  description:
    "A transparent experimental Victorian election forecast covering polls, all 88 electorates, eight Council regions, uncertainty, sources and validation.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-AU">
      <body>
        {children}
        <PartyVisualKey />
        <AnalystEvidenceGuide />
        <EvidenceFreshnessStatus />
      </body>
    </html>
  );
}
