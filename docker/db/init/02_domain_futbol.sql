SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: continent_enum; Type: TYPE; Schema: reference; Owner: -
--



--
-- Name: event_type_enum; Type: TYPE; Schema: reference; Owner: -
--



--
-- Name: position_enum; Type: TYPE; Schema: reference; Owner: -
--



--
-- Name: status_enum; Type: TYPE; Schema: reference; Owner: -
--



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: basic_stats; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.basic_stats (
    basic_stats_id integer NOT NULL,
    match_id integer NOT NULL,
    player_id integer NOT NULL,
    minutes smallint,
    goals smallint,
    assists smallint,
    touches smallint,
    passes_total smallint,
    passes_completed smallint,
    passes_accuracy smallint,
    key_passes smallint,
    crosses_total smallint,
    crosses_completed smallint,
    long_balls_total smallint,
    long_balls_completed smallint,
    shots_total smallint,
    shots_on_target smallint,
    dribbles_attempted smallint,
    dribbles_successful smallint,
    dribbles_past smallint,
    fouls_drawn smallint,
    fouls_committed smallint,
    offsides smallint,
    yellow_cards smallint,
    second_yellow_cards smallint,
    red_cards smallint,
    penalties_scored smallint,
    penalties_missed smallint,
    penalties_won smallint,
    penalties_conceded smallint,
    shots_blocked smallint,
    dribbled_past smallint,
    clearances smallint,
    interceptions smallint,
    tackles smallint,
    possession_lost smallint,
    aerials_won smallint,
    aerials_lost smallint,
    blocks smallint,
    hit_woodwork smallint,
    rating numeric(4,2),
    CONSTRAINT basic_stats_aerials_lost_check CHECK ((aerials_lost >= 0)),
    CONSTRAINT basic_stats_aerials_won_check CHECK ((aerials_won >= 0)),
    CONSTRAINT basic_stats_assists_check CHECK ((assists >= 0)),
    CONSTRAINT basic_stats_blocks_check CHECK ((blocks >= 0)),
    CONSTRAINT basic_stats_clearances_check CHECK ((clearances >= 0)),
    CONSTRAINT basic_stats_crosses_completed_check CHECK ((crosses_completed >= 0)),
    CONSTRAINT basic_stats_crosses_total_check CHECK ((crosses_total >= 0)),
    CONSTRAINT basic_stats_dribbled_past_check CHECK ((dribbled_past >= 0)),
    CONSTRAINT basic_stats_dribbles_attempted_check CHECK ((dribbles_attempted >= 0)),
    CONSTRAINT basic_stats_dribbles_past_check CHECK ((dribbles_past >= 0)),
    CONSTRAINT basic_stats_dribbles_successful_check CHECK ((dribbles_successful >= 0)),
    CONSTRAINT basic_stats_fouls_committed_check CHECK ((fouls_committed >= 0)),
    CONSTRAINT basic_stats_fouls_drawn_check CHECK ((fouls_drawn >= 0)),
    CONSTRAINT basic_stats_goals_check CHECK ((goals >= 0)),
    CONSTRAINT basic_stats_hit_woodwork_check CHECK ((hit_woodwork >= 0)),
    CONSTRAINT basic_stats_interceptions_check CHECK ((interceptions >= 0)),
    CONSTRAINT basic_stats_key_passes_check CHECK ((key_passes >= 0)),
    CONSTRAINT basic_stats_long_balls_completed_check CHECK ((long_balls_completed >= 0)),
    CONSTRAINT basic_stats_long_balls_total_check CHECK ((long_balls_total >= 0)),
    CONSTRAINT basic_stats_minutes_check CHECK ((minutes >= 0)),
    CONSTRAINT basic_stats_offsides_check CHECK ((offsides >= 0)),
    CONSTRAINT basic_stats_penalties_conceded_check CHECK ((penalties_conceded >= 0)),
    CONSTRAINT basic_stats_penalties_missed_check CHECK ((penalties_missed >= 0)),
    CONSTRAINT basic_stats_penalties_scored_check CHECK ((penalties_scored >= 0)),
    CONSTRAINT basic_stats_penalties_won_check CHECK ((penalties_won >= 0)),
    CONSTRAINT basic_stats_possession_lost_check CHECK ((possession_lost >= 0)),
    CONSTRAINT basic_stats_passes_accuracy_check CHECK (((passes_accuracy >= 0) AND (passes_accuracy <= 100))),
    CONSTRAINT basic_stats_passes_completed_check CHECK ((passes_completed >= 0)),
    CONSTRAINT basic_stats_passes_total_check CHECK ((passes_total >= 0)),
    CONSTRAINT basic_stats_rating_check CHECK (((rating >= (0)::numeric) AND (rating <= (10)::numeric))),
    CONSTRAINT basic_stats_red_cards_check CHECK ((red_cards >= 0)),
    CONSTRAINT basic_stats_second_yellow_cards_check CHECK ((second_yellow_cards >= 0)),
    CONSTRAINT basic_stats_shots_blocked_check CHECK ((shots_blocked >= 0)),
    CONSTRAINT basic_stats_shots_on_target_check CHECK ((shots_on_target >= 0)),
    CONSTRAINT basic_stats_shots_total_check CHECK ((shots_total >= 0)),
    CONSTRAINT basic_stats_tackles_check CHECK ((tackles >= 0)),
    CONSTRAINT basic_stats_touches_check CHECK ((touches >= 0)),
    CONSTRAINT basic_stats_yellow_cards_check CHECK ((yellow_cards >= 0))
);


--
-- Name: basic_stats_basic_stats_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.basic_stats_basic_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: basic_stats_basic_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: -
--

ALTER SEQUENCE core.basic_stats_basic_stats_id_seq OWNED BY core.basic_stats.basic_stats_id;


--
-- Name: competition; Type: TABLE; Schema: reference; Owner: -
--

CREATE TABLE reference.competition (
    competition_id smallint NOT NULL,
    competition_name text NOT NULL,
    country text,
    continent reference.continent_enum,
    is_international boolean DEFAULT false NOT NULL,
    default_matchdays smallint,
    notes text
);


--
-- Name: event; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.event (
    event_id integer NOT NULL,
    match_id integer NOT NULL,
    minute smallint,
    event_type reference.event_type_enum NOT NULL,
    main_player_id integer NOT NULL,
    extra_player_id integer,
    team_id integer NOT NULL,
    notes text
);


--
-- Name: match; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core."match" (
    match_id integer NOT NULL,
    matchday_id integer NOT NULL,
    local_team_id integer NOT NULL,
    away_team_id integer NOT NULL,
    local_score smallint,
    away_score smallint,
    stadium text,
    duration smallint,
    is_neutral_venue boolean DEFAULT false NOT NULL,
    is_extra_time boolean DEFAULT false NOT NULL,
    is_penalties boolean DEFAULT false NOT NULL,
    notes text
);


--
-- Name: matchday; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.matchday (
    matchday_id integer NOT NULL,
    season_id smallint NOT NULL,
    matchday_number smallint NOT NULL,
    notes text
);


--
-- Name: participation; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.participation (
    match_id integer NOT NULL,
    player_id integer NOT NULL,
    status reference.status_enum NOT NULL,
    "position" reference.position_enum,
    is_captain boolean DEFAULT false NOT NULL,
    notes text
);


--
-- Name: player; Type: TABLE; Schema: reference; Owner: -
--

CREATE TABLE reference.player (
    player_id integer NOT NULL,
    player_name text NOT NULL,
    country text,
    notes text
);


--
-- Name: season; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.season (
    season_id smallint NOT NULL,
    competition_id smallint NOT NULL,
    season_label character varying(20) NOT NULL,
    is_completed boolean DEFAULT false NOT NULL,
    notes text
);


--
-- Name: season_team; Type: TABLE; Schema: registry; Owner: -
--

CREATE TABLE registry.season_team (
    season_team_id integer NOT NULL,
    season_id smallint NOT NULL,
    team_id integer NOT NULL,
    notes text
);


--
-- Name: team; Type: TABLE; Schema: reference; Owner: -
--

CREATE TABLE reference.team (
    team_id integer NOT NULL,
    team_name text NOT NULL,
    country text,
    city text,
    stadium text,
    notes text
);


--
-- Name: team_player; Type: TABLE; Schema: registry; Owner: -
--

CREATE TABLE registry.team_player (
    season_team_id integer NOT NULL,
    player_id integer NOT NULL,
    jersey_number smallint,
    notes text
);


--
-- Name: goalie_stats; Type: TABLE; Schema: stats; Owner: -
--

CREATE TABLE stats.goalie_stats (
    basic_stats_id integer NOT NULL,
    saves smallint,
    saves_inside_box smallint,
    sweeper_actions smallint,
    punches smallint,
    high_claims smallint,
    clean_sheets smallint,
    goals_conceded smallint,
    CONSTRAINT goalie_stats_clean_sheets_check CHECK ((clean_sheets >= 0)),
    CONSTRAINT goalie_stats_goals_conceded_check CHECK ((goals_conceded >= 0)),
    CONSTRAINT goalie_stats_high_claims_check CHECK ((high_claims >= 0)),
    CONSTRAINT goalie_stats_punches_check CHECK ((punches >= 0)),
    CONSTRAINT goalie_stats_saves_check CHECK ((saves >= 0)),
    CONSTRAINT goalie_stats_saves_inside_box_check CHECK ((saves_inside_box >= 0)),
    CONSTRAINT goalie_stats_sweeper_actions_check CHECK ((sweeper_actions >= 0))
);


--
-- Name: defender_stats; Type: TABLE; Schema: stats; Owner: -
--

CREATE TABLE stats.defender_stats (
    basic_stats_id integer NOT NULL,
    clearances_attempted smallint,
    clearances_successful smallint,
    blocked_shots smallint,
    interceptions_successful smallint,
    interceptions_attempted smallint,
    aerial_duels_won smallint,
    aerial_duels_lost smallint,
    CONSTRAINT defender_stats_aerial_duels_lost_check CHECK ((aerial_duels_lost >= 0)),
    CONSTRAINT defender_stats_aerial_duels_won_check CHECK ((aerial_duels_won >= 0)),
    CONSTRAINT defender_stats_blocked_shots_check CHECK ((blocked_shots >= 0)),
    CONSTRAINT defender_stats_clearances_attempted_check CHECK ((clearances_attempted >= 0)),
    CONSTRAINT defender_stats_clearances_successful_check CHECK ((clearances_successful >= 0)),
    CONSTRAINT defender_stats_interceptions_attempted_check CHECK ((interceptions_attempted >= 0)),
    CONSTRAINT defender_stats_interceptions_successful_check CHECK ((interceptions_successful >= 0))
);


--
-- Name: midfielder_stats; Type: TABLE; Schema: stats; Owner: -
--

CREATE TABLE stats.midfielder_stats (
    basic_stats_id integer NOT NULL,
    passes_forward smallint,
    passes_backward smallint,
    progressive_passes smallint,
    key_passes_third smallint,
    switches_of_play smallint,
    CONSTRAINT midfielder_stats_key_passes_third_check CHECK ((key_passes_third >= 0)),
    CONSTRAINT midfielder_stats_passes_backward_check CHECK ((passes_backward >= 0)),
    CONSTRAINT midfielder_stats_passes_forward_check CHECK ((passes_forward >= 0)),
    CONSTRAINT midfielder_stats_progressive_passes_check CHECK ((progressive_passes >= 0)),
    CONSTRAINT midfielder_stats_switches_of_play_check CHECK ((switches_of_play >= 0))
);


--
-- Name: forward_stats; Type: TABLE; Schema: stats; Owner: -
--

CREATE TABLE stats.forward_stats (
    basic_stats_id integer NOT NULL,
    shots_inside_box smallint,
    shots_outside_box smallint,
    big_chances_missed smallint,
    dribbles_into_box smallint,
    progressive_runs smallint,
    CONSTRAINT forward_stats_big_chances_missed_check CHECK ((big_chances_missed >= 0)),
    CONSTRAINT forward_stats_dribbles_into_box_check CHECK ((dribbles_into_box >= 0)),
    CONSTRAINT forward_stats_progressive_runs_check CHECK ((progressive_runs >= 0)),
    CONSTRAINT forward_stats_shots_inside_box_check CHECK ((shots_inside_box >= 0)),
    CONSTRAINT forward_stats_shots_outside_box_check CHECK ((shots_outside_box >= 0))
);


--
-- Name: match_match_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.match_match_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: match_match_id_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: -
--

ALTER SEQUENCE core.match_match_id_seq OWNED BY core."match".match_id;


--
-- Name: event_event_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.event_event_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_event_id_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: -
--

ALTER SEQUENCE core.event_event_id_seq OWNED BY core.event.event_id;


--
-- Name: matchday_matchday_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.matchday_matchday_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: matchday_matchday_id_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: -
--

ALTER SEQUENCE core.matchday_matchday_id_seq OWNED BY core.matchday.matchday_id;


--
-- Name: season_season_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.season_season_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: season_season_id_seq; Type: SEQUENCE OWNED BY; Schema: core; Owner: -
--

ALTER SEQUENCE core.season_season_id_seq OWNED BY core.season.season_id;


--
-- Name: competition_competition_id_seq; Type: SEQUENCE; Schema: reference; Owner: -
--

CREATE SEQUENCE reference.competition_competition_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: competition_competition_id_seq; Type: SEQUENCE OWNED BY; Schema: reference; Owner: -
--

ALTER SEQUENCE reference.competition_competition_id_seq OWNED BY reference.competition.competition_id;


--
-- Name: player_player_id_seq; Type: SEQUENCE; Schema: reference; Owner: -
--

CREATE SEQUENCE reference.player_player_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: player_player_id_seq; Type: SEQUENCE OWNED BY; Schema: reference; Owner: -
--

ALTER SEQUENCE reference.player_player_id_seq OWNED BY reference.player.player_id;


--
-- Name: team_team_id_seq; Type: SEQUENCE; Schema: reference; Owner: -
--

CREATE SEQUENCE reference.team_team_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: team_team_id_seq; Type: SEQUENCE OWNED BY; Schema: reference; Owner: -
--

ALTER SEQUENCE reference.team_team_id_seq OWNED BY reference.team.team_id;


--
-- Name: season_team_season_team_id_seq; Type: SEQUENCE; Schema: registry; Owner: -
--

CREATE SEQUENCE registry.season_team_season_team_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: season_team_season_team_id_seq; Type: SEQUENCE OWNED BY; Schema: registry; Owner: -
--

ALTER SEQUENCE registry.season_team_season_team_id_seq OWNED BY registry.season_team.season_team_id;


--
-- Name: basic_stats basic_stats_id; Type: DEFAULT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.basic_stats ALTER COLUMN basic_stats_id SET DEFAULT nextval('core.basic_stats_basic_stats_id_seq'::regclass);


--
-- Name: competition competition_id; Type: DEFAULT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.competition ALTER COLUMN competition_id SET DEFAULT nextval('reference.competition_competition_id_seq'::regclass);


--
-- Name: event event_id; Type: DEFAULT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.event ALTER COLUMN event_id SET DEFAULT nextval('core.event_event_id_seq'::regclass);


--
-- Name: match match_id; Type: DEFAULT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."match" ALTER COLUMN match_id SET DEFAULT nextval('core.match_match_id_seq'::regclass);


--
-- Name: matchday matchday_id; Type: DEFAULT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.matchday ALTER COLUMN matchday_id SET DEFAULT nextval('core.matchday_matchday_id_seq'::regclass);


--
-- Name: player player_id; Type: DEFAULT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.player ALTER COLUMN player_id SET DEFAULT nextval('reference.player_player_id_seq'::regclass);


--
-- Name: season season_id; Type: DEFAULT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.season ALTER COLUMN season_id SET DEFAULT nextval('core.season_season_id_seq'::regclass);


--
-- Name: season_team season_team_id; Type: DEFAULT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.season_team ALTER COLUMN season_team_id SET DEFAULT nextval('registry.season_team_season_team_id_seq'::regclass);


--
-- Name: team team_id; Type: DEFAULT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.team ALTER COLUMN team_id SET DEFAULT nextval('reference.team_team_id_seq'::regclass);


--
-- Name: continent_enum; Type: COMMENT; Schema: reference; Owner: -
--

COMMENT ON TYPE reference.continent_enum IS 'Continent classification used for competitions';


--
-- Name: event_type_enum; Type: COMMENT; Schema: reference; Owner: -
--

COMMENT ON TYPE reference.event_type_enum IS 'Normalized event types for football matches';


--
-- Name: position_enum; Type: COMMENT; Schema: reference; Owner: -
--

COMMENT ON TYPE reference.position_enum IS 'Positions used in participation and basic stats';


--
-- Name: status_enum; Type: COMMENT; Schema: reference; Owner: -
--

COMMENT ON TYPE reference.status_enum IS 'Participation status codes';


--
-- Name: competition competition_name_unique; Type: CONSTRAINT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.competition
    ADD CONSTRAINT competition_name_unique UNIQUE (competition_name);


--
-- Name: competition competition_pkey; Type: CONSTRAINT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.competition
    ADD CONSTRAINT competition_pkey PRIMARY KEY (competition_id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (event_id);


--
-- Name: matchday matchday_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.matchday
    ADD CONSTRAINT matchday_pkey PRIMARY KEY (matchday_id);


--
-- Name: match match_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."match"
    ADD CONSTRAINT match_pkey PRIMARY KEY (match_id);


--
-- Name: participation participation_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.participation
    ADD CONSTRAINT participation_pkey PRIMARY KEY (match_id, player_id);


--
-- Name: player player_pkey; Type: CONSTRAINT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.player
    ADD CONSTRAINT player_pkey PRIMARY KEY (player_id);


--
-- Name: season season_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.season
    ADD CONSTRAINT season_pkey PRIMARY KEY (season_id);


--
-- Name: season_team season_team_pkey; Type: CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.season_team
    ADD CONSTRAINT season_team_pkey PRIMARY KEY (season_team_id);


--
-- Name: team team_name_unique; Type: CONSTRAINT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.team
    ADD CONSTRAINT team_name_unique UNIQUE (team_name);


--
-- Name: team team_pkey; Type: CONSTRAINT; Schema: reference; Owner: -
--

ALTER TABLE ONLY reference.team
    ADD CONSTRAINT team_pkey PRIMARY KEY (team_id);


--
-- Name: unique_match_per_matchday; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."match"
    ADD CONSTRAINT unique_match_per_matchday UNIQUE (matchday_id, local_team_id, away_team_id);


--
-- Name: unique_matchday_per_season; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.matchday
    ADD CONSTRAINT unique_matchday_per_season UNIQUE (season_id, matchday_number);


--
-- Name: unique_player_per_match; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.basic_stats
    ADD CONSTRAINT unique_player_per_match UNIQUE (match_id, player_id);


--
-- Name: unique_season_label_per_competition; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.season
    ADD CONSTRAINT unique_season_label_per_competition UNIQUE (competition_id, season_label);


--
-- Name: unique_team_per_season; Type: CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.season_team
    ADD CONSTRAINT unique_team_per_season UNIQUE (season_id, team_id);


--
-- Name: basic_stats_basic_stats_id_key; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.basic_stats
    ADD CONSTRAINT basic_stats_basic_stats_id_key UNIQUE (basic_stats_id);


--
-- Name: basic_stats_pkey; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.basic_stats
    ADD CONSTRAINT basic_stats_pkey PRIMARY KEY (basic_stats_id);


--
-- Name: goalie_stats_pkey; Type: CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.goalie_stats
    ADD CONSTRAINT goalie_stats_pkey PRIMARY KEY (basic_stats_id);


--
-- Name: defender_stats_pkey; Type: CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.defender_stats
    ADD CONSTRAINT defender_stats_pkey PRIMARY KEY (basic_stats_id);


--
-- Name: midfielder_stats_pkey; Type: CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.midfielder_stats
    ADD CONSTRAINT midfielder_stats_pkey PRIMARY KEY (basic_stats_id);


--
-- Name: forward_stats_pkey; Type: CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.forward_stats
    ADD CONSTRAINT forward_stats_pkey PRIMARY KEY (basic_stats_id);


--
-- Name: team_player_pkey; Type: CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.team_player
    ADD CONSTRAINT team_player_pkey PRIMARY KEY (season_team_id, player_id);


--
-- Name: basic_stats_match_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.basic_stats
    ADD CONSTRAINT basic_stats_match_fk FOREIGN KEY (match_id) REFERENCES core."match"(match_id) ON DELETE CASCADE;


--
-- Name: basic_stats_player_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.basic_stats
    ADD CONSTRAINT basic_stats_player_fk FOREIGN KEY (player_id) REFERENCES reference.player(player_id) ON DELETE CASCADE;


--
-- Name: defender_stats_basic_stats_fk; Type: FK CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.defender_stats
    ADD CONSTRAINT defender_stats_basic_stats_fk FOREIGN KEY (basic_stats_id) REFERENCES core.basic_stats(basic_stats_id) ON DELETE CASCADE;


--
-- Name: event_match_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.event
    ADD CONSTRAINT event_match_fk FOREIGN KEY (match_id) REFERENCES core."match"(match_id) ON DELETE CASCADE;


--
-- Name: event_main_player_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.event
    ADD CONSTRAINT event_main_player_fk FOREIGN KEY (main_player_id) REFERENCES reference.player(player_id) ON DELETE CASCADE;


--
-- Name: event_extra_player_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.event
    ADD CONSTRAINT event_extra_player_fk FOREIGN KEY (extra_player_id) REFERENCES reference.player(player_id) ON DELETE SET NULL;


--
-- Name: event_team_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.event
    ADD CONSTRAINT event_team_fk FOREIGN KEY (team_id) REFERENCES reference.team(team_id) ON DELETE CASCADE;


--
-- Name: goalie_stats_basic_stats_fk; Type: FK CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.goalie_stats
    ADD CONSTRAINT goalie_stats_basic_stats_fk FOREIGN KEY (basic_stats_id) REFERENCES core.basic_stats(basic_stats_id) ON DELETE CASCADE;


--
-- Name: match_away_team_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."match"
    ADD CONSTRAINT match_away_team_fk FOREIGN KEY (away_team_id) REFERENCES reference.team(team_id) ON DELETE CASCADE;


--
-- Name: match_local_team_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."match"
    ADD CONSTRAINT match_local_team_fk FOREIGN KEY (local_team_id) REFERENCES reference.team(team_id) ON DELETE CASCADE;


--
-- Name: match_matchday_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core."match"
    ADD CONSTRAINT match_matchday_fk FOREIGN KEY (matchday_id) REFERENCES core.matchday(matchday_id) ON DELETE CASCADE;


--
-- Name: matchday_season_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.matchday
    ADD CONSTRAINT matchday_season_fk FOREIGN KEY (season_id) REFERENCES core.season(season_id) ON DELETE CASCADE;


--
-- Name: midfielder_stats_basic_stats_fk; Type: FK CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.midfielder_stats
    ADD CONSTRAINT midfielder_stats_basic_stats_fk FOREIGN KEY (basic_stats_id) REFERENCES core.basic_stats(basic_stats_id) ON DELETE CASCADE;


--
-- Name: participation_match_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.participation
    ADD CONSTRAINT participation_match_fk FOREIGN KEY (match_id) REFERENCES core."match"(match_id) ON DELETE CASCADE;


--
-- Name: participation_player_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.participation
    ADD CONSTRAINT participation_player_fk FOREIGN KEY (player_id) REFERENCES reference.player(player_id) ON DELETE CASCADE;


--
-- Name: season_competition_fk; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.season
    ADD CONSTRAINT season_competition_fk FOREIGN KEY (competition_id) REFERENCES reference.competition(competition_id) ON DELETE CASCADE;


--
-- Name: season_team_season_fk; Type: FK CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.season_team
    ADD CONSTRAINT season_team_season_fk FOREIGN KEY (season_id) REFERENCES core.season(season_id) ON DELETE CASCADE;


--
-- Name: season_team_team_fk; Type: FK CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.season_team
    ADD CONSTRAINT season_team_team_fk FOREIGN KEY (team_id) REFERENCES reference.team(team_id) ON DELETE CASCADE;


--
-- Name: team_player_player_fk; Type: FK CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.team_player
    ADD CONSTRAINT team_player_player_fk FOREIGN KEY (player_id) REFERENCES reference.player(player_id) ON DELETE CASCADE;


--
-- Name: team_player_season_team_fk; Type: FK CONSTRAINT; Schema: registry; Owner: -
--

ALTER TABLE ONLY registry.team_player
    ADD CONSTRAINT team_player_season_team_fk FOREIGN KEY (season_team_id) REFERENCES registry.season_team(season_team_id) ON DELETE CASCADE;


--
-- Name: forward_stats_basic_stats_fk; Type: FK CONSTRAINT; Schema: stats; Owner: -
--

ALTER TABLE ONLY stats.forward_stats
    ADD CONSTRAINT forward_stats_basic_stats_fk FOREIGN KEY (basic_stats_id) REFERENCES core.basic_stats(basic_stats_id) ON DELETE CASCADE;


--
-- Name: idx_basic_stats_match_player; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_basic_stats_match_player ON core.basic_stats USING btree (match_id, player_id);


--
-- Name: idx_event_match_minute; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_event_match_minute ON core.event USING btree (match_id, minute);


--
-- Name: idx_match_season; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_match_season ON core."match" USING btree (matchday_id);


--
-- Name: idx_participation_match_player; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_participation_match_player ON core.participation USING btree (match_id, player_id);


--
-- Name: idx_season_competition; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_season_competition ON core.season USING btree (competition_id);


--
-- Name: idx_season_team; Type: INDEX; Schema: registry; Owner: -
--

CREATE INDEX idx_season_team ON registry.season_team USING btree (season_id, team_id);


--
-- Name: idx_team_player; Type: INDEX; Schema: registry; Owner: -
--

CREATE INDEX idx_team_player ON registry.team_player USING btree (season_team_id, player_id);


--
-- Name: idx_player_name; Type: INDEX; Schema: reference; Owner: -
--

CREATE INDEX idx_player_name ON reference.player USING btree (player_name);


--
-- Name: idx_team_name; Type: INDEX; Schema: reference; Owner: -
--

CREATE INDEX idx_team_name ON reference.team USING btree (team_name);


--
-- Name: function: get_match_basic_stats; Type: FUNCTION; Schema: core;
--

CREATE OR REPLACE FUNCTION core.get_match_basic_stats(p_match_id integer)
RETURNS TABLE (
    match_id integer,
    player_id integer,
    minutes smallint,
    goals smallint,
    assists smallint,
    rating numeric(4,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        bs.match_id,
        bs.player_id,
        bs.minutes,
        bs.goals,
        bs.assists,
        bs.rating
    FROM core.basic_stats bs
    WHERE bs.match_id = p_match_id;
END;
$$;


--
-- Name: raw.match; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw."match" (
    match_id integer NOT NULL,
    competition text NOT NULL,
    season text NOT NULL,
    matchday integer,
    local_team_id integer NOT NULL,
    away_team_id integer NOT NULL,
    local_score integer,
    away_score integer,
    stadium text,
    duration integer,
    source_system text,
    source_url text,
    ran_at timestamp with time zone,
    raw_run_id uuid NOT NULL,
    CONSTRAINT raw_match_matchday_check CHECK ((matchday > 0)),
    CONSTRAINT raw_match_duration_check CHECK ((duration > 0))
);


--
-- Name: raw.player_match; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.player_match (
    match_id integer NOT NULL,
    player_id integer NOT NULL,
    team_id integer NOT NULL,
    jersey_number integer,
    position text,
    status integer,
    CONSTRAINT raw_player_match_status_check CHECK ((status >= 0))
);


--
-- Name: raw.player_match_stat; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.player_match_stat (
    match_id integer NOT NULL,
    player_id integer NOT NULL,
    stat_name text NOT NULL,
    raw_value text NOT NULL,
    value_numeric double precision,
    value_ratio_num integer,
    value_ratio_den integer,
    CONSTRAINT raw_player_match_stat_value_ratio_den_check CHECK ((value_ratio_den >= 0)),
    CONSTRAINT raw_player_match_stat_value_ratio_num_check CHECK ((value_ratio_num >= 0))
);


--
-- Name: raw.player_match player_match_pkey; Type: CONSTRAINT; Schema: raw; Owner: -
--

ALTER TABLE ONLY raw.player_match
    ADD CONSTRAINT player_match_pkey PRIMARY KEY (match_id, player_id);


--
-- Name: raw.player_match_stat player_match_stat_pkey; Type: CONSTRAINT; Schema: raw; Owner: -
--

ALTER TABLE ONLY raw.player_match_stat
    ADD CONSTRAINT player_match_stat_pkey PRIMARY KEY (match_id, player_id, stat_name);


--
-- Name: raw.match raw_match_pkey; Type: CONSTRAINT; Schema: raw; Owner: -
--

ALTER TABLE ONLY raw."match"
    ADD CONSTRAINT raw_match_pkey PRIMARY KEY (match_id);


--
-- Name: raw.player_match match_id_idx; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX player_match_match_id_idx
    ON raw.player_match (match_id);


--
-- Name: raw.player_match_stat match_id_idx; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX player_match_stat_match_id_idx
    ON raw.player_match_stat (match_id);


--
-- Name: raw.player_match player_match_player_id_idx; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX player_match_player_id_idx
    ON raw.player_match (player_id);


--
-- Name: raw.player_match_stat player_match_stat_player_id_idx; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX player_match_stat_player_id_idx
    ON raw.player_match_stat (player_id);


--
-- Name: raw.player_match_stat player_match_stat_stat_name_idx; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX player_match_stat_stat_name_idx
    ON raw.player_match_stat (stat_name);


-- =========================================================================
-- Tablas de la capa raw
-- =========================================================================

CREATE TABLE raw.error (
    error_id      serial PRIMARY KEY,
    raw_run_id    uuid        NOT NULL,
    competition   text,
    season        text,
    match_id      integer,
    match_url     text,
    error         text,
    traceback     text,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX error_comp_season_idx
    ON raw.error (competition, season);

CREATE INDEX error_run_idx
    ON raw.error (raw_run_id);


CREATE TABLE raw.target (
    target_id         bigserial PRIMARY KEY,

    competition       text NOT NULL,
    season            text NOT NULL,

    -- Puede ser NULL si la fuente aún no tiene id estable
    match_id          integer,

    match_url         text NOT NULL,

    -- Para ligas: jornada; para copas puede ser NULL
    matchday          integer,

    -- Reservados para copas / torneos
    stage_name        text,
    leg_number        smallint,

    discovered_at     timestamptz NOT NULL DEFAULT now(),
    discovered_run_id uuid        NOT NULL,

    ignore_manually   boolean     NOT NULL DEFAULT false,
    ignore_reason     text
);

-- Por simplicidad y compatibilidad con:
--   ON CONFLICT (competition, season, match_id)
-- usamos un índice UNIQUE completo (no parcial).
-- Las filas con match_id NULL pueden repetirse.
DROP INDEX IF EXISTS raw_target_match_unique;

CREATE UNIQUE INDEX raw_target_match_unique
    ON raw.target (competition, season, match_id);

CREATE INDEX raw_target_comp_season_matchday_idx
    ON raw.target (competition, season, matchday);

CREATE INDEX raw_target_url_idx
    ON raw.target (match_url);


CREATE OR REPLACE VIEW raw.v_target_status AS
SELECT
    t.target_id,
    t.competition,
    t.season,
    t.match_id,
    t.match_url,
    t.matchday,
    t.stage_name,
    t.leg_number,
    t.ignore_manually,
    t.ignore_reason,
    m.match_id IS NOT NULL AS in_match,
    CASE
        WHEN t.ignore_manually THEN 'ignored'
        WHEN m.match_id IS NOT NULL THEN 'ok'
        WHEN e.error_id IS NOT NULL THEN 'error'
        ELSE 'pending'
    END AS status,
    t.discovered_at,
    t.discovered_run_id
FROM raw.target t
LEFT JOIN raw."match" m
  ON m.match_id    = t.match_id
 AND m.competition = t.competition
 AND m.season      = t.season
LEFT JOIN LATERAL (
    SELECT error_id
    FROM raw.error e
    WHERE e.match_id    = t.match_id
      AND e.competition = t.competition
      AND e.season      = t.season
    ORDER BY e.created_at DESC
    LIMIT 1
) e ON TRUE;
