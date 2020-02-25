#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

import os

import pyutilib
import pyutilib.th as unittest

from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.solvers.plugins.solvers.CPLEX import CPLEXSHELL, MockCPLEX, _validate_file_name


class _mock_cplex_128(object):
    def version(self):
        return (12,8,0)

class _mock_cplex_126(object):
    def version(self):
        return (12,6,0)

class CPLEX_utils(unittest.TestCase):
    def test_validate_file_name(self):
        _126 = _mock_cplex_126()
        _128 = _mock_cplex_128()

        # Check plain file
        fname = 'foo.lp'
        self.assertEqual(fname, _validate_file_name(_126, fname, 'xxx'))
        self.assertEqual(fname, _validate_file_name(_128, fname, 'xxx'))

        # Check spaces in the file
        fname = 'foo bar.lp'
        with self.assertRaisesRegexp(
                ValueError, "Space detected in CPLEX xxx file"):
            _validate_file_name(_126, fname, 'xxx')
        self.assertEqual('"%s"' % (fname,),
                         _validate_file_name(_128, fname, 'xxx'))

        # check OK path separators
        fname = 'foo%sbar.lp' % (os.path.sep,)
        self.assertEqual(fname, _validate_file_name(_126, fname, 'xxx'))
        self.assertEqual(fname, _validate_file_name(_128, fname, 'xxx'))

        # check BAD path separators
        bad_char = '/\\'.replace(os.path.sep,'')
        fname = 'foo%sbar.lp' % (bad_char,)
        msg = 'Unallowed character \(%s\) found in CPLEX xxx file' % (
            repr(bad_char)[1:-1],)
        with self.assertRaisesRegexp(ValueError, msg):
            _validate_file_name(_126, fname, 'xxx')
        with self.assertRaisesRegexp(ValueError, msg):
            _validate_file_name(_128, fname, 'xxx')



class TestCPLEXSHELLProcessLogfile(unittest.TestCase):
    def setUp(self):
        solver = MockCPLEX()
        solver._log_file = pyutilib.services.TempfileManager.create_tempfile(
            suffix=".log"
        )
        self.solver = solver

    def tearDown(self):
        pyutilib.services.TempfileManager.clear_tempfiles()

    def test_log_file_shows_no_solution(self):
        log_file_text = """
MIP - Time limit exceeded, no integer solution.
Current MIP best bound =  0.0000000000e+00 (gap is infinite)
Solution time =    0.00 sec.  Iterations = 0  Nodes = 0
Deterministic time = 0.00 ticks  (0.20 ticks/sec)

CPLEX> CPLEX Error  1217: No solution exists.
No file written.
CPLEX>"""
        with open(self.solver._log_file, "w") as f:
            f.write(log_file_text)

        results = CPLEXSHELL.process_logfile(self.solver)
        self.assertEqual(results.solver.status, SolverStatus.error)
        self.assertEqual(
            results.solver.termination_condition, TerminationCondition.noSolution
        )
        self.assertEqual(
            results.solver.termination_message,
            "MIP - Time limit exceeded, no integer solution.",
        )
        self.assertEqual(results.solver.return_code, 1217)

    def test_log_file_shows_infeasible(self):
        log_file_text = """
MIP - Integer infeasible.
Current MIP best bound =  0.0000000000e+00 (gap is infinite)
Solution time =    0.00 sec.  Iterations = 0  Nodes = 0
Deterministic time = 0.00 ticks  (0.20 ticks/sec)

CPLEX> CPLEX Error  1217: No solution exists.
No file written.
CPLEX>"""
        with open(self.solver._log_file, "w") as f:
            f.write(log_file_text)

        results = CPLEXSHELL.process_logfile(self.solver)
        self.assertEqual(results.solver.status, SolverStatus.error)
        self.assertEqual(
            results.solver.termination_condition, TerminationCondition.infeasible
        )
        self.assertEqual(
            results.solver.termination_message, "MIP - Integer infeasible."
        )
        self.assertEqual(results.solver.return_code, 1217)


if __name__ == "__main__":
    unittest.main()
