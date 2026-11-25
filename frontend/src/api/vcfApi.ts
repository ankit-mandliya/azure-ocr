import { vcfApi } from './axios';

export interface VCFContact {
  full_name: string | null;
  company: string | null;
  job_title: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  address: string | null;
  notes: string | null;
}

export interface VCFPreviewResponse {
  filename: string;
  total_contacts: number;
  contacts: VCFContact[];
}

export async function previewVCF(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<VCFPreviewResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await vcfApi.post<VCFPreviewResponse>('/vcf/preview', formData, {
    onUploadProgress: (event) => {
      if (!onProgress) return;
      const percent = event.total ? Math.round((event.loaded * 100) / event.total) : 0;
      onProgress(percent);
    },
  });

  return data;
}
