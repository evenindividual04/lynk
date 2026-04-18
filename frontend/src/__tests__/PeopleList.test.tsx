import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import PeopleList from "../pages/PeopleList";
import type { PeopleListResponse } from "../types/api";

const EMPTY_RESPONSE: PeopleListResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: 50,
};

const WITH_PEOPLE: PeopleListResponse = {
  items: [
    {
      id: 1,
      linkedin_url: "https://www.linkedin.com/in/alice/",
      full_name: "Alice Smith",
      first_name: "Alice",
      last_name: "Smith",
      headline: "Engineer at Acme",
      location: null,
      connected_date: "2024-01-01",
      current_company_id: null,
      current_position_title: "Engineer",
      email: null,
      priority: 0,
      stage: "not_contacted",
      source: "csv_import",
      created_at: "2024-01-01T00:00:00",
      updated_at: "2024-01-01T00:00:00",
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
};

const server = setupServer(
  http.get("/api/people", () => HttpResponse.json(EMPTY_RESPONSE)),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function setup() {
  render(
    <QueryClientProvider client={makeClient()}>
      <MemoryRouter>
        <PeopleList />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PeopleList", () => {
  it("shows empty state when no people", async () => {
    setup();
    await waitFor(() =>
      expect(screen.getByText(/no people found/i)).toBeInTheDocument(),
    );
  });

  it("shows people table when data available", async () => {
    server.use(http.get("/api/people", () => HttpResponse.json(WITH_PEOPLE)));
    setup();
    await waitFor(() =>
      expect(screen.getByText("Alice Smith")).toBeInTheDocument(),
    );
    expect(screen.getByText("Engineer")).toBeInTheDocument();
  });

  it("shows total count", async () => {
    server.use(http.get("/api/people", () => HttpResponse.json(WITH_PEOPLE)));
    setup();
    await waitFor(() => expect(screen.getByText("1 total")).toBeInTheDocument());
  });

  it("shows error when API fails", async () => {
    server.use(
      http.get("/api/people", () => HttpResponse.error()),
    );
    setup();
    await waitFor(() =>
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument(),
    );
  });
});
