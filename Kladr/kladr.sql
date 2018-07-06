--
-- PostgreSQL database dump
--

-- Dumped from database version 10.4
-- Dumped by pg_dump version 10.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: wt_kladr_objects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wt_kladr_objects (
    id bigint NOT NULL,
    title text NOT NULL,
    kladr_code text,
    kladr_ocatd text,
    kladr_index text,
    type_id bigint,
    parent_id bigint,
    deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public.wt_kladr_objects OWNER TO postgres;

--
-- Name: wt_kladr_objects_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wt_kladr_objects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.wt_kladr_objects_id_seq OWNER TO postgres;

--
-- Name: wt_kladr_objects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wt_kladr_objects_id_seq OWNED BY public.wt_kladr_objects.id;


--
-- Name: wt_kladr_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wt_kladr_types (
    id bigint NOT NULL,
    short_title text,
    title text NOT NULL,
    level integer,
    kladr_code integer
);


ALTER TABLE public.wt_kladr_types OWNER TO postgres;

--
-- Name: wt_kladr_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wt_kladr_types_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.wt_kladr_types_id_seq OWNER TO postgres;

--
-- Name: wt_kladr_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wt_kladr_types_id_seq OWNED BY public.wt_kladr_types.id;


--
-- Name: wt_kladr_objects id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_objects ALTER COLUMN id SET DEFAULT nextval('public.wt_kladr_objects_id_seq'::regclass);


--
-- Name: wt_kladr_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_types ALTER COLUMN id SET DEFAULT nextval('public.wt_kladr_types_id_seq'::regclass);


--
-- Name: wt_kladr_types kladr_code_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_types
    ADD CONSTRAINT kladr_code_unique UNIQUE (kladr_code);


--
-- Name: wt_kladr_objects wt_kladr_objects_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_objects
    ADD CONSTRAINT wt_kladr_objects_pk PRIMARY KEY (id);


--
-- Name: wt_kladr_types wt_kladr_types_pk1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_types
    ADD CONSTRAINT wt_kladr_types_pk1 PRIMARY KEY (id);


--
-- Name: fki_wt_kladr_objects_fk1; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_wt_kladr_objects_fk1 ON public.wt_kladr_objects USING btree (type_id);


--
-- Name: fki_wt_kladr_objects_fk2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_wt_kladr_objects_fk2 ON public.wt_kladr_objects USING btree (parent_id);


--
-- Name: wt_kladr_objects_idx1; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_objects_idx1 ON public.wt_kladr_objects USING btree (title);


--
-- Name: wt_kladr_objects_idx2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_objects_idx2 ON public.wt_kladr_objects USING btree (kladr_code);


--
-- Name: wt_kladr_objects_idx3; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_objects_idx3 ON public.wt_kladr_objects USING btree (kladr_ocatd);


--
-- Name: wt_kladr_objects_idx4; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_objects_idx4 ON public.wt_kladr_objects USING btree (kladr_index);


--
-- Name: wt_kladr_objects_idx5; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_objects_idx5 ON public.wt_kladr_objects USING btree (deleted);


--
-- Name: wt_kladr_types_idx1; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_types_idx1 ON public.wt_kladr_types USING btree (short_title);


--
-- Name: wt_kladr_types_idx2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_types_idx2 ON public.wt_kladr_types USING btree (title);


--
-- Name: wt_kladr_types_idx3; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_types_idx3 ON public.wt_kladr_types USING btree (level);


--
-- Name: wt_kladr_types_idx4; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX wt_kladr_types_idx4 ON public.wt_kladr_types USING btree (kladr_code);


--
-- Name: wt_kladr_objects wt_kladr_objects_fk1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_objects
    ADD CONSTRAINT wt_kladr_objects_fk1 FOREIGN KEY (type_id) REFERENCES public.wt_kladr_types(id);


--
-- Name: wt_kladr_objects wt_kladr_objects_fk2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wt_kladr_objects
    ADD CONSTRAINT wt_kladr_objects_fk2 FOREIGN KEY (parent_id) REFERENCES public.wt_kladr_objects(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

