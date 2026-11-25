export interface ExtractedValue {
  value: string | null;
  confidence: number | null;
}

export interface AzureBusinessCard {
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  company_name: string | null;
  department: string | null;
  job_title: string | null;
  emails: ExtractedValue[];
  websites: ExtractedValue[];
  mobile_phones: ExtractedValue[];
  work_phones: ExtractedValue[];
  other_phones: ExtractedValue[];
  fax_numbers: ExtractedValue[];
  addresses: ExtractedValue[];
}

export interface AzureExtractionResponse {
  success: boolean;
  cards: AzureBusinessCard[];
  overall_confidence: number | null;
  metadata: {
    provider: string;
    model_id: string;
    timestamp: string;
    status: string;
  };
}
