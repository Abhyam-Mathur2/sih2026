# AI matching

Local normalization expands abbreviations and normalizes dimensions. Rules extract product type, DN size, material grade, pressure rating and connection. Sentence Transformers provides locally cached semantic embeddings and RapidFuzz supplies lexical matching. The configurable weighted score is semantic 35%, fuzzy 20%, attributes 25%, technical 20%. A contradiction on a critical valve attribute caps a score below `NEAR_DUPLICATE`: DN50 and DN100 can never be `IDENTICAL`.
