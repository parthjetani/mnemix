# Fix Plan — Code Review Issues

## Priority Order

- [x] 1. Port consistency — standardize on 8000 (uvicorn default, cli.py already uses it)
- [ ] 2. extractor.py — fix return type annotation `-> int` → `tuple[int, list[MemoryCreate]]`
- [ ] 3. extractor.py — remove premature `status="complete"` inside `process_ingestion_pipeline` (caller handles final status)
- [ ] 4. api/ingest.py — reuse `job` reference instead of re-fetching after `db.flush()`
- [ ] 5. main.py — pre-load memory retriever in lifespan
- [ ] 6. models/schemas.py — add Literal category validation to `MemoryAddRequest`

## Notes
- Port: cli.py says 8000, docs say 8080. Fix docs (not code).
- Bug 3 root: process_ingestion_pipeline sets status="complete" before caller saves memories to DB.
  Caller (_run_ai_export_ingestion) then sets complete again. Remove final block from extractor.py.
- Segmenter blocking embed: acceptable for demo, add TODO comment only.
