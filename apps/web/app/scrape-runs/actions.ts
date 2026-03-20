"use server";

import { revalidatePath } from "next/cache";

import { getApiBaseUrl } from "@/lib/api";


export async function createScrapeRun(formData: FormData) {
  const source = String(formData.get("source") || "dice");
  const query = String(formData.get("query") || "");
  const location = String(formData.get("location") || "Remote");
  const maxPages = Number(formData.get("max_pages") || 1);

  await fetch(`${getApiBaseUrl()}/scrape-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source,
      query: query || null,
      location: location || null,
      max_pages: maxPages,
    }),
  });

  revalidatePath("/scrape-runs");
  revalidatePath("/jobs");
}
