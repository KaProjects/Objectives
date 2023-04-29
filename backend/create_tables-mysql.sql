create table if not exists PValues ( id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                    name text not null,
                                    description text not null);

create table if not exists Objectives ( id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                        value_id INTEGER,
                                        FOREIGN KEY (value_id) REFERENCES PValues(id),
                                        state text not null,
                                        name text not null,
                                        description text not null,
                                        date_created text not null,
                                        date_finished text not null);

create table if not exists KeyResults ( id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                        objective_id INTEGER,
                                        FOREIGN KEY (objective_id) REFERENCES Objectives(id),
                                        state text not null,
                                        name text not null,
                                        description text not null,
                                        s text not null,
                                        m text not null,
                                        a text not null,
                                        r text not null,
                                        t text not null,
                                        date_created text not null,
                                        date_reviewed text not null);

create table if not exists Tasks ( id INTEGER PRIMARY KEY AUTO_INCREMENT,
                                    kr_id INTEGER,
                                    FOREIGN KEY (kr_id) REFERENCES KeyResults(id),
                                    state text not null,
                                    value text not null);

