CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";


create table users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    password text not null,
    is_admin boolean default false,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);


create table tasks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete set null,
    title text not null,
    description text,
    status text not null 
        check (status in ('created', 'in_process', 'completed')) 
        default 'created',
    total_minutes float default 0.0,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

create table resume_snippets (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    profile_summary text not null,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now(),
    fts tsvector GENERATED ALWAYS AS (to_tsvector('english', profile_summary)) STORED,
    embedding vector(768) not null
);

CREATE INDEX resume_snippets_summary_fts_idx ON resume_snippets USING gin (fts);
CREATE INDEX resume_snippets_summary_hnsw_idx ON resume_snippets USING hnsw (embedding vector_cosine_ops);