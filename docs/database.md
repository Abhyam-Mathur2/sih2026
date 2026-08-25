# Database

Core entities are `cpses`, `users`, `material_categories`, `materials`, `material_attributes`, `material_embeddings`, `material_matches`, `national_materials`, `material_mappings`, `upload_jobs`, and `audit_logs`. Alembic migration `001_initial_schema` creates constraints and the pgvector IVFFlat index.

```mermaid
erDiagram
 CPSE ||--o{ MATERIAL : owns
 MATERIAL ||--o{ MATERIAL_ATTRIBUTE : has
 MATERIAL ||--o{ MATERIAL_MATCH : source_or_candidate
 NATIONAL_MATERIAL ||--o{ MATERIAL_MAPPING : standardizes
 MATERIAL ||--o{ MATERIAL_MAPPING : maps
 USER ||--o{ AUDIT_LOG : creates
```
