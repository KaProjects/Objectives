insert into PValues(id, name, description) values (1, "Zdravie", "his project is served and bundled with Vite ... out Cypress and Cypress Component Testing.");
insert into PValues(id, name, description) values (2, "Second", "ha");
insert into PValues(id, name, description) values (3, "Third", "with objectives");
insert into PValues(id, name, description) values (4, "Modifable", "x");

insert into Objectives(id, value_id, state, name, description) values (1, 3, "achieved", "obj1", "some description");
insert into Objectives(id, value_id, state, name, description) values (2, 3, "active", "obj2", "some other description");
insert into Objectives(id, value_id, state, name, description) values (3, 3, "failed", "obj3", "third description");
insert into Objectives(id, value_id, state, name, description) values (4, 4, "active", "Add More", "test kr inserts");
insert into Objectives(id, value_id, state, name, description) values (5, 4, "active", "To Clear", "test kr deletions");
insert into Objectives(id, value_id, state, name, description) values (6, 4, "active", "Needs Tasks", "test task add/del");

insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (1, 1, "completed", "x", "xx", "s", "m", "a", "r", "t", "10/03/2023", "11/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (2, 2, "completed", "aaa with description", "description is here", "s", "m", "a", "r", "t", "10/03/2023", "10/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (3, 2, "failed", "bbb", "", "", "", "", "", "", "10/03/2023", "12/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (4, 2, "active", "ccc", "", "", "", "", "", "", "10/03/2023", "13/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (5, 3, "failed", "y", "yy", "s", "m", "a", "r", "t", "10/03/2023", "14/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (6, 4, "active", "add one more", "", "", "", "", "", "", "10/03/2023", "12/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (7, 5, "active", "should stay", "", "", "", "", "", "", "10/03/2023", "12/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (8, 5, "active", "to del", "", "", "", "", "", "", "10/03/2023", "12/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (9, 6, "active", "no change", "", "", "", "", "", "", "10/03/2023", "12/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (10, 6, "active", "add task", "", "", "", "", "", "", "10/03/2023", "12/03/2023");
insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values (11, 6, "active", "del task", "", "", "", "", "", "", "10/03/2023", "12/03/2023");

insert into Tasks(id, kr_id, state, value) values (1, 3, "failed", "task1");
insert into Tasks(id, kr_id, state, value) values (2, 4, "active", "task2.0");
insert into Tasks(id, kr_id, state, value) values (3, 2, "finished", "task3");
insert into Tasks(id, kr_id, state, value) values (4, 4, "finished", "task2.1");
insert into Tasks(id, kr_id, state, value) values (5, 4, "failed", "task2.2");
insert into Tasks(id, kr_id, state, value) values (6, 1, "finished", "achieved obj task");
insert into Tasks(id, kr_id, state, value) values (7, 5, "failed", "failed obj task");
insert into Tasks(id, kr_id, state, value) values (8, 9, "active", "no change");
insert into Tasks(id, kr_id, state, value) values (9, 10, "active", "add one more");
insert into Tasks(id, kr_id, state, value) values (10, 11, "active", "should stay");
insert into Tasks(id, kr_id, state, value) values (11, 11, "active", "to del");