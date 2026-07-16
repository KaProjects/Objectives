-- Upgrade an existing Objectives database from schema 1.2 to 1.3.
--
-- Take a backup before running this migration. It will fail safely if existing
-- rows contain NULL parent IDs or refer to a missing parent record.
--
-- The old schema creates unnamed InnoDB foreign keys. MySQL assigns those
-- deterministic names as <table>_ibfk_1, which are replaced below with named
-- constraints that delete dependent records together with their parent.

ALTER TABLE Objectives
    DROP FOREIGN KEY Objectives_ibfk_1,
    MODIFY COLUMN value_id INTEGER NOT NULL,
    ADD CONSTRAINT fk_objectives_value
        FOREIGN KEY (value_id) REFERENCES PValues(id) ON DELETE CASCADE;

ALTER TABLE KeyResults
    DROP FOREIGN KEY KeyResults_ibfk_1,
    MODIFY COLUMN objective_id INTEGER NOT NULL,
    ADD CONSTRAINT fk_key_results_objective
        FOREIGN KEY (objective_id) REFERENCES Objectives(id) ON DELETE CASCADE;

ALTER TABLE Tasks
    DROP FOREIGN KEY Tasks_ibfk_1,
    MODIFY COLUMN kr_id INTEGER NOT NULL,
    ADD CONSTRAINT fk_tasks_key_result
        FOREIGN KEY (kr_id) REFERENCES KeyResults(id) ON DELETE CASCADE;

ALTER TABLE ObjectiveIdeas
    DROP FOREIGN KEY ObjectiveIdeas_ibfk_1,
    MODIFY COLUMN objective_id INTEGER NOT NULL,
    ADD CONSTRAINT fk_objective_ideas_objective
        FOREIGN KEY (objective_id) REFERENCES Objectives(id) ON DELETE CASCADE;
