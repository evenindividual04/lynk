import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { ImportResponse } from "../types/api";

export default function ImportUpload() {
  const [result, setResult] = useState<ImportResponse | null>(null);

  const mutation = useMutation({
    mutationFn: (file: File) => api.upload<ImportResponse>("/api/imports", file),
    onSuccess: (data) => setResult(data),
  });

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) mutation.mutate(accepted[0]);
    },
    [mutation],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    multiple: false,
  });

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">Import LinkedIn CSV</h1>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-indigo-400 bg-indigo-50"
            : "border-gray-300 hover:border-indigo-300 hover:bg-gray-50"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-gray-500 text-sm">
          {isDragActive
            ? "Drop your LinkedIn CSV here…"
            : "Drag & drop your LinkedIn CSV, or click to select"}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Export from LinkedIn → Settings → Data Privacy → Get a copy of your data
        </p>
      </div>

      {mutation.isPending && (
        <p className="text-center text-gray-400 animate-pulse">Importing…</p>
      )}

      {mutation.isError && (
        <p className="text-red-500 text-sm text-center">
          Import failed. Please check the file and try again.
        </p>
      )}

      {result && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
          <h2 className="font-semibold text-gray-800">Import complete</h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-green-50 rounded p-3">
              <p className="text-2xl font-bold text-green-600">{result.imported}</p>
              <p className="text-xs text-gray-500">New</p>
            </div>
            <div className="bg-blue-50 rounded p-3">
              <p className="text-2xl font-bold text-blue-600">{result.merged}</p>
              <p className="text-xs text-gray-500">Merged</p>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <p className="text-2xl font-bold text-gray-500">{result.skipped}</p>
              <p className="text-xs text-gray-500">Skipped</p>
            </div>
          </div>

          {result.errors.length > 0 && (
            <div>
              <p className="text-sm text-red-600 font-medium mb-1">
                {result.errors.length} errors (first 10 shown):
              </p>
              <ul className="text-xs space-y-1">
                {result.errors.map((e, i) => (
                  <li key={i} className="text-red-500">
                    Row {e.row}: {e.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
