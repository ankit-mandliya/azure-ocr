export interface ContactFields {
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  contact_number: string | null;
  company_name: string | null;
  job_title: string | null;
  website: string | null;
  address: string | null;
}

export interface Contact extends ContactFields {
  id: string;
  created_at: string;
  needs_review: boolean | null;
  overall_confidence: number | null;
  warnings: string[];
}

export type ContactInput = ContactFields;

export interface OCRPreview extends ContactFields {
  overall_confidence: number | null;
  needs_review: boolean;
  warnings: string[];
}

export const emptyContact: ContactInput = {
  first_name: '',
  last_name: '',
  email: '',
  contact_number: '',
  company_name: '',
  job_title: '',
  website: '',
  address: '',
};
