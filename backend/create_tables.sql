create table if not exists PValues ( id INTEGER PRIMARY KEY,
                                    name text not null,
                                    description text not null);

create table if not exists Objectives ( id INTEGER PRIMARY KEY,
                                        value_id INTEGER references PValues( id ),
                                        state text not null,
                                        name text not null,
                                        description text not null);

create table if not exists KeyResults ( id INTEGER PRIMARY KEY,
                                        objective_id INTEGER references Objectives( id ),
                                        state text not null,
                                        name text not null,
                                        description text not null,
                                        s text not null,
                                        m text not null,
                                        a text not null,
                                        r text not null,
                                        t text not null);

create table if not exists Tasks ( id INTEGER PRIMARY KEY,
                                    kr_id INTEGER references KeyResults( id ),
                                    state text not null,
                                    value text not null);

