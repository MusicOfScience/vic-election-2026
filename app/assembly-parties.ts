export type Party = "ALP" | "LIB_NAT" | "ONP" | "GRN" | "OTH_IND";

export const parties: Party[] = ["ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND"];
export const partyMeta: Record<Party, { label: string; short: string; css: string; colour: string }> = {
  ALP: { label: "Labor", short: "ALP", css: "labor", colour: "#d84a42" },
  LIB_NAT: { label: "Coalition", short: "L–NP", css: "coalition", colour: "#2e63ad" },
  ONP: { label: "One Nation", short: "ONP", css: "onp", colour: "#6e4da0" },
  GRN: { label: "Greens", short: "GRN", css: "greens", colour: "#159867" },
  OTH_IND: { label: "Other / independent", short: "OTH", css: "other", colour: "#d19b2a" },
};
