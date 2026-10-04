// Shared with Home.tsx (category tiles) and Products.tsx (filter dropdown),
// so "Hoodies" means the same thing everywhere on the site.
export const CATEGORY_ORDER = [
  "T-Shirts",
  "Hoodies",
  "Crewnecks",
  "Sweatshirts",
  "Quarter/Full-Zips",
  "Jackets",
  "Other",
];

export function categorize(garmentType: string): string {
  const t = garmentType.toLowerCase();
  if (t.includes("hood")) return "Hoodies";
  if (t.includes("zip")) return "Quarter/Full-Zips";
  if (t.includes("jacket")) return "Jackets";
  if (t.includes("crew")) return "Crewnecks";
  if (t.includes("t-shirt") || t.includes("tee")) return "T-Shirts";
  if (t.includes("sweatshirt") || t.includes("mockneck")) return "Sweatshirts";
  return "Other";
}
