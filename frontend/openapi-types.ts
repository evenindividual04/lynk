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

// Phase 2: Outreach types

export type Scenario =
  | "ps_outreach"
  | "research_gsoc"
  | "referral_request"
  | "info_call"
  | "alumni"
  | "founder";

export type Channel = "li_connection_note" | "li_dm" | "cold_email";

export type MessageStatus = "draft" | "queued" | "sent" | "failed" | "cancelled";

export type FollowUpKind = "nudge_opened" | "nudge_unopened" | "final_bump";

export type FollowUpStatus = "pending" | "completed" | "cancelled";

export interface TemplateVersionRead {
  id: number;
  template_id: number;
  version: number;
  subject_template: string | null;
  body_template: string;
  notes: string | null;
  created_at: string;
}

export interface TemplateRead {
  id: number;
  name: string;
  scenario: Scenario;
  channel: Channel;
  active_version_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface TemplateDetail extends TemplateRead {
  versions: TemplateVersionRead[];
}

export interface MessageRead {
  id: number;
  person_id: number;
  template_version_id: number | null;
  channel: Channel;
  status: MessageStatus;
  subject: string | null;
  body: string;
  tracking_id: string;
  scheduled_for: string | null;
  sent_at: string | null;
  error: string | null;
  thread_id: string | null;
  parent_message_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SendResponse {
  message: MessageRead;
  sending_enabled: boolean;
  warning: string | null;
}

export interface FollowUpTaskRead {
  id: number;
  person_id: number;
  parent_message_id: number;
  kind: FollowUpKind;
  scheduled_for: string;
  status: FollowUpStatus;
  generated_message_id: number | null;
  created_at: string;
}
