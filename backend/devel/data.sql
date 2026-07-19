-- Local development data. This file is loaded only by devel/run.py.

insert into PValues(id, name, description) values
  (1, 'Health', 'Energy, movement, recovery, and sustainable habits.'),
  (2, 'Career', 'Building useful skills and doing meaningful work.'),
  (3, 'Finances', 'A stable foundation and deliberate investing.'),
  (4, 'Relationships', 'Time and attention for the people who matter.'),
  (5, 'Personal growth', 'Learning, creativity, and reflection.');

insert into Objectives(id, value_id, state, name, description, date_created, date_finished) values
  (1, 1, 'active', 'Feel energetic throughout the week', 'Build a routine that supports good sleep, regular movement, and focused work.', '2026-07-01', ''),
  (2, 1, 'active', 'Build strength without burnout', 'Train consistently while leaving enough room for recovery.', '2026-06-15', ''),
  (3, 1, 'failed', 'Run a spring half marathon', 'This was paused after an injury; keep it as a useful historical example.', '2026-02-01', '2026-04-20'),
  (4, 2, 'active', 'Deliver a stronger portfolio', 'Turn recent work into a concise portfolio and ask for actionable feedback.', '2026-07-05', ''),
  (5, 2, 'achieved', 'Complete the architecture course', 'Finish the course and capture the key practices to apply at work.', '2026-03-01', '2026-06-10'),
  (6, 3, 'active', 'Build a six-month emergency fund', 'Automate saving and review monthly spending.', '2026-05-01', ''),
  (7, 4, 'active', 'Be more present with family', 'Create regular space for conversations and shared time.', '2026-07-10', ''),
  (8, 5, 'active', 'Read with intention', 'Keep a small, realistic reading habit and record useful ideas.', '2026-07-12', ''),
  (9, 1, 'achieved', 'Establish a consistent sleep routine', 'A previous successful health objective, kept as an example of a completed outcome.', '2026-01-05', '2026-02-14'),
  (10, 1, 'achieved', 'Cook dinner at home on weekdays', 'Plan simple meals and reduce last-minute takeaway decisions.', '2026-02-01', '2026-03-31'),
  (11, 1, 'achieved', 'Complete a month of daily mobility work', 'Ten minutes of mobility after the morning routine.', '2026-03-01', '2026-04-02'),
  (12, 1, 'failed', 'Avoid all sugar for a month', 'The goal was too restrictive and not sustainable.', '2026-01-10', '2026-01-24'),
  (13, 1, 'failed', 'Train six days every week', 'The training volume left too little recovery time.', '2026-03-15', '2026-04-05'),
  (14, 1, 'failed', 'Meditate for an hour every day', 'The starting commitment was unrealistic for the schedule.', '2026-04-01', '2026-04-18'),
  (15, 1, 'achieved', 'Build a regular walking habit', 'A first successful attempt at making movement part of the week.', '2023-04-01', '2023-06-30'),
  (16, 1, 'failed', 'Do yoga every morning for 90 days', 'The routine was too ambitious for travel and busy mornings.', '2023-08-01', '2023-09-12'),
  (17, 1, 'achieved', 'Reduce weekday caffeine', 'Replace the afternoon coffee with tea or water.', '2024-01-10', '2024-03-20'),
  (18, 1, 'failed', 'Run a marathon in autumn', 'The plan did not leave enough time to build mileage safely.', '2024-06-01', '2024-10-05'),
  (19, 1, 'achieved', 'Eat vegetables with lunch every weekday', 'Make vegetables the default part of weekday lunches.', '2025-02-01', '2025-04-30'),
  (20, 1, 'failed', 'Never use a screen after 20:00', 'The absolute rule did not work with occasional evening plans.', '2025-09-01', '2025-10-15');

insert into KeyResults(id, objective_id, state, name, description, s, m, a, r, t, date_created, date_reviewed) values
  (1, 1, 'active', 'Average at least 7.5 hours of sleep', 'Track sleep on work nights and adjust the evening routine.', 'true', 'Weekly average is at least 7.5 hours', 'Keep a consistent 23:00 bedtime', 'true', '2026-07-10', '2026-07-01', '2026-07-16'),
  (2, 1, 'active', 'Walk 8,000 steps on five days each week', 'Use a lunch walk and short evening walk as defaults.', 'true', 'Five days per week reach 8,000 steps', 'Start with four days if a week is busy', 'true', '2026-07-19', '2026-07-01', '2026-07-18'),
  (3, 1, 'completed', 'Prepare a simple weekday breakfast plan', 'Three repeatable breakfasts are prepared in advance.', 'true', 'Three recipes are written and ingredients are available', 'Use familiar recipes only', 'true', '2026-07-15', '2026-07-01', '2026-07-14'),
  (4, 2, 'active', 'Complete two full-body strength sessions weekly', 'Focus on a small routine that is easy to repeat.', 'true', 'Two sessions are logged each week for six weeks', 'Use 30-minute sessions', 'true', '2026-09-01', '2026-06-15', '2026-07-17'),
  (5, 2, 'active', 'Log a short recovery note after every session', 'Note soreness, sleep, and whether the next session should change.', 'true', 'A note exists after every completed session', 'Use a one-minute template', 'true', '', '2026-06-15', '2026-07-17'),
  (6, 3, 'failed', 'Run 15 km without stopping', 'Training was interrupted by an injury.', 'true', 'Complete one 15 km run', 'Resume only after recovery', 'true', 'by the end of spring', '2026-02-01', '2026-04-20'),
  (7, 4, 'active', 'Publish three portfolio case studies', 'Each case study explains the problem, decisions, and outcome.', 'true', 'Three public case studies are published', 'Reuse existing project material', 'true', '2026-08-31', '2026-07-05', '2026-07-18'),
  (8, 4, 'active', 'Ask two peers for portfolio feedback', 'Send a focused request with specific questions.', 'true', 'Two feedback conversations are completed', 'Choose peers who know the work', 'true', '2026-08-10', '2026-07-05', '2026-07-12'),
  (9, 5, 'completed', 'Finish the architecture course', 'All modules, exercises, and notes are complete.', 'true', 'Course completion certificate and summary notes', 'Schedule two focused sessions weekly', 'true', '2026-06-01', '2026-03-01', '2026-06-10'),
  (10, 6, 'active', 'Save 12,000 EUR for emergencies', 'Automate the transfer on payday.', 'true', 'Emergency account balance reaches 12,000 EUR', 'Start with the current monthly surplus', 'true', '2026-12-31', '2026-05-01', '2026-07-01'),
  (11, 6, 'active', 'Review spending at the end of each month', 'Classify spending and decide one adjustment for the next month.', 'true', 'One review is completed each month', 'Use the existing bank export', 'true', '', '2026-05-01', '2026-06-30'),
  (12, 7, 'active', 'Plan one shared activity each week', 'Choose a simple activity together and protect the time.', 'true', 'One shared activity happens every week for two months', 'Keep activities local and low effort', 'true', '2026-09-15', '2026-07-10', '2026-07-17'),
  (13, 8, 'active', 'Read six books this quarter', 'Alternate fiction and non-fiction and note one useful takeaway.', 'true', 'Six finished books are recorded', 'Read 20 minutes before bed', 'true', '2026-09-30', '2026-07-12', '2026-07-18'),
  (14, 8, 'active', 'Write a short note for every finished book', 'Capture an idea worth applying or discussing.', 'true', 'One note exists for every finished book', 'Use a three-sentence template', 'true', '', '2026-07-12', '2026-07-12'),
  (15, 9, 'completed', 'Walk 7,000 steps on four days each week', 'The walking routine became stable by the end of the quarter.', 'true', 'Four days each week reach 7,000 steps', 'Use the commute and lunch break', 'true', '2023-06-30', '2023-04-01', '2023-06-30'),
  (16, 9, 'completed', 'Plan one longer weekend walk each month', 'A low-pressure way to explore nearby places.', 'true', 'Three longer walks are completed', 'Invite a friend when possible', 'true', '2023-06-30', '2023-04-01', '2023-06-28'),
  (17, 10, 'failed', 'Complete 90 morning yoga sessions', 'The initial target did not account for travel and recovery days.', 'true', 'Ninety sessions are logged', 'Use a ten-minute routine', 'true', '2023-10-30', '2023-08-01', '2023-09-12'),
  (18, 11, 'completed', 'Replace afternoon coffee on four weekdays', 'The new routine reduced late-day caffeine.', 'true', 'Four weekdays each week use tea or water', 'Keep tea at the desk', 'true', '2024-03-20', '2024-01-10', '2024-03-20'),
  (19, 12, 'failed', 'Complete a 30 km long run', 'The mileage increase was too aggressive.', 'true', 'One 30 km run is completed comfortably', 'Increase distance gradually', 'true', '2024-09-30', '2024-06-01', '2024-10-05'),
  (20, 13, 'completed', 'Prepare vegetables for five weekday lunches', 'A simple Sunday preparation routine made lunch easier.', 'true', 'Five lunches include prepared vegetables each week', 'Use frozen vegetables when needed', 'true', '2025-04-30', '2025-02-01', '2025-04-30'),
  (21, 13, 'completed', 'Try six new vegetable-based recipes', 'The recipe list now has several reliable favourites.', 'true', 'Six recipes are cooked and rated', 'Cook one recipe each weekend', 'true', '2025-04-30', '2025-02-01', '2025-04-22'),
  (22, 14, 'failed', 'Keep every evening screen-free after 20:00', 'The rule was not flexible enough for real life.', 'true', 'Thirty consecutive screen-free evenings', 'Allow exceptions for planned events', 'true', '2025-10-01', '2025-09-01', '2025-10-15');

insert into Tasks(id, kr_id, state, value) values
  (1, 1, 'finished', 'Set a 22:30 evening reminder'),
  (2, 1, 'active', 'Keep phone outside the bedroom'),
  (3, 2, 'finished', 'Walk after lunch on Monday'),
  (4, 2, 'active', 'Plan the Friday evening walk'),
  (5, 4, 'active', 'Schedule Tuesday strength session'),
  (6, 4, 'active', 'Schedule Saturday strength session'),
  (7, 7, 'finished', 'Select the first portfolio project'),
  (8, 7, 'active', 'Draft the case study outline'),
  (9, 10, 'active', 'Confirm the automated monthly transfer'),
  (10, 12, 'active', 'Suggest a weekend walk'),
  (11, 13, 'active', 'Choose the next book');

insert into ObjectiveIdeas(id, objective_id, value) values
  (1, 1, 'Try a short evening stretching routine'),
  (2, 4, 'Add a before-and-after section to each case study'),
  (3, 7, 'Create a shared list of low-effort activity ideas');
