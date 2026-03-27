"use server";

import { revalidatePath } from "next/cache";

import { getApiBaseUrl } from "@/lib/api";


export async function generateResume(jobId: string) {
  const response = await fetch(`${getApiBaseUrl()}/jobs/${jobId}/documents/resume`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to start resume generation.");
  }
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/documents");
}


export async function generateCoverLetter(jobId: string) {
  const response = await fetch(`${getApiBaseUrl()}/jobs/${jobId}/documents/cover-letter`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to start cover letter generation.");
  }
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/documents");
}


export async function applyToJob(jobId: string) {
  const response = await fetch(`${getApiBaseUrl()}/jobs/${jobId}/apply`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to start apply flow.");
  }
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/applications");
}
