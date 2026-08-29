"use client";

import { useRef, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { CircleHelp, X } from "lucide-react";

const items = [
  ["labor", "Labor"],
  ["coalition", "Coalition / Liberal"],
  ["national", "Nationals"],
  ["greens", "Greens"],
  ["one-nation", "One Nation"],
  ["independent", "Independent"],
  ["teal-independent", "Teal-aligned independent"],
  ["other", "Other party"],
] as const;

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

export function PartyVisualKey() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const isClient = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
  const target = isClient ? document.querySelector(".dashboard-tabs-list") : null;

  const open = () => dialogRef.current?.showModal();
  const close = () => dialogRef.current?.close();

  return (
    <>
      {target && createPortal(
        <button type="button" className="how-to-read-trigger" onClick={open} aria-haspopup="dialog">
          <CircleHelp size={16} />How to read
        </button>,
        target,
      )}
      <dialog ref={dialogRef} className="how-to-read-dialog" onClick={(event) => { if (event.target === dialogRef.current) close(); }}>
        <div className="how-to-read-panel">
          <div className="how-to-read-head">
            <div><p className="eyebrow">Reading the forecast</p><h2>How to read</h2></div>
            <button type="button" className="how-to-read-close" onClick={close} aria-label="Close how-to-read guide"><X size={18} /></button>
          </div>
          <div className="guide-grid how-to-read-terms">
            <article><strong>Win chance</strong><p>How often a party won in 5,000 simulated elections—not its predicted vote share.</p></article>
            <article><strong>Likely range</strong><p>The middle 80% of simulated results. About one in five model runs falls outside it.</p></article>
            <article><strong>Middle result</strong><p>The median: half the simulations finish above it and half below it.</p></article>
            <article><strong>First preference</strong><p>The number 1 vote before preferences from eliminated candidates are distributed.</p></article>
            <article><strong>Final two</strong><p>The two candidates left after the preferential count eliminates the others.</p></article>
            <article><strong>Swing</strong><p>The change in a party’s two-party vote from one election to the next, in percentage points.</p></article>
          </div>
          <section className="party-key-body" aria-labelledby="party-key-heading">
            <div className="party-key-heading"><p className="eyebrow">Visual language</p><h3 id="party-key-heading">Party colours &amp; chart marks</h3></div>
            <div className="party-key-grid">
              {items.map(([css, label]) => (
                <div className="party-key-item" key={css}>
                  <i className={`party-swatch ${css}`} aria-hidden="true" />
                  <span>{label}</span>
                </div>
              ))}
            </div>
            <p className="party-key-note">
              Nationals use very dark green with a yellow diagonal accent; on line charts the yellow becomes an outline/halo and marker cue. Independents use neutral slate. A teal-aligned independent remains an independent and carries a teal accent. Labels and line styles remain visible so colour is never the only cue.
            </p>
          </section>
        </div>
      </dialog>
    </>
  );
}
