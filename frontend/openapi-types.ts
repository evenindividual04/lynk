// Auto-generated from /openapi.json — run `pnpm gen:types` to regenerate
// This is a manually maintained stub until the backend is running in CI.

export type Stage =
  | "not_contacted"
  | "contacted_li"
  | "contacted_email"
  | "contacted_both"
  | "opened"
  | "replied"
  | "call_scheduled"
  | "offer"
  | "rejected"
  | "bounced"
  | "cold"
  | "opted_out";

export type Source = "csv_import" | "manual" | "discovery";

export interface PersonRead {
  id: number;
  linkedin_url: string;
  full_name: string;
  first_name: string;
  last_name: string;
  headline: string | null;
  location: string | null;
  connected_date: string | null;
  current_company_id: number | null;
  current_position_title: string | null;
  email: string | null;
  priority: number;
  stage: Stage;
  source: Source;
  created_at: string;
  updated_at: string;
}

export interface TagRead {
  id: number;
  name: string;
  color: string | null;
}

export interface NoteRead {
  id: number;
  person_id: number;
  body: string;
  created_at: string;
}

export interface PersonDetail extends PersonRead {
  tags: TagRead[];
  notes: NoteRead[];
}

export interface PeopleListResponse {
  items: PersonRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface CompanyRead {
  id: number;
  name: string;
  domain: string | null;
}

export interface ImportResponse {
  imported: number;
  merged: number;
  skipped: number;
  errors: { row: string; error: string }[];
}
