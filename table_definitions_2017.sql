DROP SCHEMA IF EXISTS Draft2017 CASCADE;
-- DROP TABLE IF EXISTS DraftPick;
-- DROP TABLE IF EXISTS FantasyOwner;
-- DROP TABLE IF EXISTS Player;
-- DROP TABLE IF EXISTS FantasyLeague;

CREATE SCHEMA Draft2017;

CREATE TABLE Draft2017.FantasyLeague (
	league_id integer PRIMARY KEY,
	league_name text,
	year smallint,
	draft_type text,
	num_teams smallint,
	scoring_type text,
	roster_size smallint,
	num_starters smallint,
	num_bench smallint,
	ppr_points real,
	keepers smallint
);

CREATE TABLE Draft2017.Player (
	player_id integer PRIMARY KEY,
	player_name text,
	position text,
	team text
);

CREATE TABLE Draft2017.FantasyOwner (
	owner_id smallint,
	league_id integer REFERENCES Draft2017.FantasyLeague(league_id),
	team_name text,
	wins smallint,
	losses smallint,
	ties smallint,
	pts_scored integer,
	pts_against integer,
	PRIMARY KEY (league_id, owner_id)
);

CREATE TABLE Draft2017.DraftPick (
	league_id integer REFERENCES Draft2017.FantasyLeague(league_id),
	owner_id smallint,
	FOREIGN KEY (league_id, owner_id)
	REFERENCES Draft2017.FantasyOwner(league_id, owner_id),
	pick_number integer,
	round_number smallint,
	player_id integer REFERENCES Draft2017.Player(player_id),
	keeper boolean,
	PRIMARY KEY (league_id, pick_number)
);
