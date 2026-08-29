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

export function PartyVisualKey() {
  return (
    <details className="party-visual-key">
      <summary>
        <span>Party colours & visual key</span>
        <small>Open key</small>
      </summary>
      <div className="party-key-body">
        <div className="party-key-grid">
          {items.map(([css, label]) => (
            <div className="party-key-item" key={css}>
              <i className={`party-swatch ${css}`} aria-hidden="true" />
              <span>{label}</span>
            </div>
          ))}
        </div>
        <p className="party-key-note">
          Independents use a neutral slate. A teal-aligned independent remains an independent: the slate block carries a narrow teal stripe rather than becoming a separate party colour. “Other / independent” model aggregates remain neutral because they combine unlike candidates.
        </p>
      </div>
    </details>
  );
}
