"use client";

import { useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { CircleAlert } from "lucide-react";
import { pollSeries } from "./poll-data.generated";
import manualEvidence from "../metadata/manual-source-evidence-2026.json";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

function readableDate(value: string) {
  return new Intl.DateTimeFormat("en-AU", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(value));
}

export function EvidenceFreshnessStatus() {
  const isClient = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
  if (!isClient) return null;

  const modelEnd = pollSeries.at(-1)?.fieldworkEnd ?? null;
  const staged = [...manualEvidence.records]
    .filter((record) => record.kind === "poll" && record.status === "quarantined-awaiting-review")
    .sort((a, b) => b.fieldworkEnd.localeCompare(a.fieldworkEnd))[0];
  const newerEvidence = Boolean(staged && modelEnd && staged.fieldworkEnd > modelEnd);
  if (!staged || !newerEvidence || !modelEnd) return null;

  const operationsTarget = document.querySelector(".operations-grid");
  const releaseTarget = document.querySelector(".release-ledger");

  return <>
    {operationsTarget && createPortal(
      <article className="evidence-freshness-card">
        <CircleAlert size={17} />
        <span>Newer poll evidence</span>
        <strong>{readableDate(staged.fieldworkEnd)}</strong>
        <small>{staged.pollster} · staged for review, not yet in the model</small>
      </article>,
      operationsTarget,
    )}
    {releaseTarget && createPortal(
      <div className="evidence-freshness-callout" role="note" aria-label="Polling freshness explanation">
        <CircleAlert size={18} />
        <div>
          <strong>Why the polling freshness gate is closed</strong>
          <p>{staged.pollster} evidence ending {readableDate(staged.fieldworkEnd)} is newer than the admitted model polling ending {readableDate(modelEnd)}. It has been captured from the cited primary source and staged for review; it cannot refresh the forecast until evidence acceptance and model eligibility are explicitly approved.</p>
        </div>
      </div>,
      releaseTarget,
    )}
  </>;
}
