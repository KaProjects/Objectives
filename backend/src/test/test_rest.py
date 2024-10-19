import unittest

import test_key_results_api
import test_objectives_api
import test_tasks_api
import test_values_api

aaa = unittest.TextTestRunner(verbosity=1)

aaa.run(unittest.TestLoader().loadTestsFromModule(test_values_api))

aaa.run(unittest.TestLoader().loadTestsFromModule(test_objectives_api))

aaa.run(unittest.TestLoader().loadTestsFromModule(test_key_results_api))

aaa.run(unittest.TestLoader().loadTestsFromModule(test_tasks_api))
