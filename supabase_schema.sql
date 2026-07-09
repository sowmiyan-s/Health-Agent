-- 🩺 HIA (Health Insights Agent) Supabase Schema Configuration
-- Paste this script into your Supabase SQL Editor to set up all tables and security policies.

-- Enable UUID generation extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------------
-- 1. TABLES
------------------------------------------------------------------

-- Users profile table (linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

------------------------------------------------------------------
-- 2. INDEXES (for performance optimization)
------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);

------------------------------------------------------------------
-- 3. AUTOMATIC SYNC FROM AUTH TO PUBLIC USERS
------------------------------------------------------------------

-- Create trigger function to sync new auth users to public users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name)
    VALUES (
        new.id, 
        new.email, 
        COALESCE(new.raw_user_meta_data->>'name', '')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Bind the trigger function to the auth.users table
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

------------------------------------------------------------------
-- 4. ROW LEVEL SECURITY (RLS) POLICIES
------------------------------------------------------------------

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
CREATE POLICY "Allow users to view their own profile" 
    ON public.users FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Allow users to update their own profile" 
    ON public.users FOR UPDATE 
    USING (auth.uid() = id);

CREATE POLICY "Allow users to insert their own profile" 
    ON public.users FOR INSERT 
    WITH CHECK (true);

-- Chat Sessions Policies
CREATE POLICY "Allow users to view their own chat sessions" 
    ON public.chat_sessions FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Allow users to insert their own chat sessions" 
    ON public.chat_sessions FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow users to update their own chat sessions" 
    ON public.chat_sessions FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Allow users to delete their own chat sessions" 
    ON public.chat_sessions FOR DELETE 
    USING (auth.uid() = user_id);

-- Chat Messages Policies
CREATE POLICY "Allow users to view messages from their own sessions" 
    ON public.chat_messages FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.chat_sessions s 
            WHERE s.id = chat_messages.session_id 
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Allow users to insert messages to their own sessions" 
    ON public.chat_messages FOR INSERT 
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.chat_sessions s 
            WHERE s.id = chat_messages.session_id 
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Allow users to delete messages from their own sessions" 
    ON public.chat_messages FOR DELETE 
    USING (
        EXISTS (
            SELECT 1 FROM public.chat_sessions s 
            WHERE s.id = chat_messages.session_id 
            AND s.user_id = auth.uid()
        )
    );
