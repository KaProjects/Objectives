import unittest

import test_key_results_api
import test_objectives_api
import test_tasks_api
import test_values_api

rest_tests = unittest.TextTestRunner(verbosity=1)

rest_tests.run(unittest.TestLoader().loadTestsFromModule(test_values_api))

rest_tests.run(unittest.TestLoader().loadTestsFromModule(test_objectives_api))

rest_tests.run(unittest.TestLoader().loadTestsFromModule(test_key_results_api))

rest_tests.run(unittest.TestLoader().loadTestsFromModule(test_tasks_api))
