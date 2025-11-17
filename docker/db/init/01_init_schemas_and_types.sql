CREATE SCHEMA core;

CREATE SCHEMA reference;

CREATE SCHEMA registry;

CREATE SCHEMA stats;

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TYPE reference.continent_enum AS ENUM (
    'Africa',
    'Asia',
    'Europe',
    'NorthAmerica',
    'SouthAmerica',
    'AustraliaInternation'
);

CREATE TYPE reference.event_type_enum AS ENUM (
    'Substitution',
    'Goal',
    'Yellow card',
    'Second yellow card',
    'Red card',
    'Own goal',
    'Penalty',
    'Penalty missed',
    'Disallowed goal'
);

CREATE TYPE reference.position_enum AS ENUM (
    'GK',
    'DF',
    'MF',
    'FW',
    'MNG'
);

CREATE TYPE reference.status_enum AS ENUM (
    'starter',
    'substitute',
    'unused',
    'other'
);
