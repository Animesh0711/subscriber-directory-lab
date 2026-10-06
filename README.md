# Subscriber Directory Lab — browser edition

Runs the original Python skip list, chained hash table and sorted-array algorithms in a Pyodide web worker. No Python server or installation is needed by visitors.

## GitHub Pages
Publish the repository main branch, root folder, in Settings > Pages.
Keep index.html, worker.js, bridge.py and source/ together. Paths work under a repository URL.

## Use
Wait for Ready, then Generate & build. Use Search & update for exact/range queries and insert/delete. Export downloads a ZIP containing CSV and an index snapshot. The benchmark uses independent fixed datasets and can take several minutes. Download its results separately.

This edition starts with no benchmark result. Browser timings are measured on the visitor device, not copied from the desktop report. Dataset changes and results exist only in the open tab until exported. A reload clears them. Imported CSVs are processed locally; they are not uploaded to a server. The Python engine loads from jsDelivr (Pyodide 0.28.1), so initial startup needs internet. Synthetic data only.

Local preview: python -m http.server 8766 then open http://localhost:8766. Opening index.html as a file is unsupported because workers and source fetches need HTTP.

Created for Animesh Pattnaik with OpenAI Codex assistance.
