import { api } from './axios';
import type { OCRPreview } from '../types/contact';

export async function previewCard(file: File, languageProfile: string): Promise<OCRPreview> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language_profile', languageProfile);
  const { data } = await api.post<OCRPreview>('/contacts/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
