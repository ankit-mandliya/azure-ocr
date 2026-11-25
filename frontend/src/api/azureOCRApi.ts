import { vcfApi } from './axios';
import type { AzureExtractionResponse } from '../types/azureOCR';

export interface AzureReviewedContact {
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  contact_number: string | null;
  company_name: string | null;
  department: string | null;
  address: string | null;
  job_title: string | null;
  website: string | null;
}

export async function getAzureOCRStatus(): Promise<{ configured: boolean; provider: string; model: string }> {
  const { data } = await vcfApi.get('/azure-ocr/status');
  return data;
}

export async function extractAzureBusinessCard(file: File): Promise<AzureExtractionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await vcfApi.post<AzureExtractionResponse>('/azure-ocr/extract', formData);
  return data;
}

export async function saveAzureContact(payload: AzureReviewedContact) {
  const { data } = await vcfApi.post('/azure-ocr/save-contact', payload);
  return data;
}
