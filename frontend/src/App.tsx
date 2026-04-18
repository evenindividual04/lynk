import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { queryClient } from "./lib/queryClient";
import Layout from "./components/Layout";
import PeopleList from "./pages/PeopleList";
import PersonDetail from "./pages/PersonDetail";
import PersonNew from "./pages/PersonNew";
import ImportUpload from "./pages/ImportUpload";
import TemplatesList from "./pages/TemplatesList";
import TemplateDetail from "./pages/TemplateDetail";
import MessagesOutbox from "./pages/MessagesOutbox";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/people" replace />} />
            <Route path="people" element={<PeopleList />} />
            <Route path="people/new" element={<PersonNew />} />
            <Route path="people/:id" element={<PersonDetail />} />
            <Route path="imports" element={<ImportUpload />} />
            <Route path="templates" element={<TemplatesList />} />
            <Route path="templates/:id" element={<TemplateDetail />} />
            <Route path="messages" element={<MessagesOutbox />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
