"use server";

import { revalidatePath } from "next/cache";

import { apiBaseUrl } from "@/lib/api";


export async function generateResume(jobId: string) {
  await fetch(`${apiBaseUrl}/jobs/${jobId}/documents/resume`, { method: "POST" });
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/documents");
}


export async function generateCoverLetter(jobId: string) {
  await fetch(`${apiBaseUrl}/jobs/${jobId}/documents/cover-letter`, { method: "POST" });
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/documents");
}


export async function applyToJob(jobId: string) {
  await fetch(`${apiBaseUrl}/jobs/${jobId}/apply`, { method: "POST" });
  revalidatePath(`/jobs/${jobId}`);
  revalidatePath("/applications");
}
