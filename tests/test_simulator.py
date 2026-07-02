"""
execute/simulator.py is the interactive console simulator: module-level globals
(network, wait_list, organ_list, selected_strategy) hold state, and each menu function
calls input() one or more times. Tests reset those globals before each test and feed
canned input() responses via monkeypatch, rather than driving the real console.
"""
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import simulator  # noqa: E402

from network_simulator.allocation import STRATEGIES  # noqa: E402
from network_simulator.OrganList import OrganList  # noqa: E402
from network_simulator.WaitList import WaitList  # noqa: E402


def _feed_inputs(monkeypatch, *responses):
    """Makes successive input() calls return each of `responses` in order."""
    iterator = iter(responses)
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(iterator))


def setup_function():
    """Resets module-level state before every test - simulator.py has no fixture hook."""
    simulator.network = None
    simulator.wait_list = WaitList()
    simulator.organ_list = OrganList()
    simulator.selected_strategy = STRATEGIES['baseline']


def test_build_network_creates_a_network_of_the_requested_size(monkeypatch):
    _feed_inputs(monkeypatch, '5', 'n')

    simulator.build_network()

    assert simulator.network is not None
    assert len(simulator.network.network_dict) == 5


def test_build_network_handles_invalid_node_count(monkeypatch, capsys):
    _feed_inputs(monkeypatch, 'not a number')

    simulator.build_network()

    assert simulator.network is None
    assert 'ValueError' in capsys.readouterr().out


def test_build_network_prompts_before_clearing_an_existing_network(monkeypatch):
    _feed_inputs(monkeypatch, '5', 'n')
    simulator.build_network()
    assert simulator.network is not None

    # a second call with an existing network asks to confirm clearing first
    _feed_inputs(monkeypatch, 'n')
    simulator.build_network()
    assert len(simulator.network.network_dict) == 5  # unchanged - declined to clear


def test_generate_patients_requires_a_network_first(capsys):
    simulator.generate_patients()

    out = capsys.readouterr().out
    assert 'no network' in out
    assert len(simulator.wait_list.wait_list) == 0


def test_generate_patients_populates_the_wait_list(monkeypatch):
    _feed_inputs(monkeypatch, '5', 'n')
    simulator.build_network()

    _feed_inputs(monkeypatch, '10', 'n')
    simulator.generate_patients()

    assert len(simulator.wait_list.wait_list) == 10


def test_harvest_organs_requires_a_network(capsys):
    simulator.harvest_organs()

    assert 'no network' in capsys.readouterr().out.lower()
    assert len(simulator.organ_list.organ_list) == 0


def test_harvest_organs_requires_patients_on_the_wait_list(capsys):
    simulator.network = simulator.GraphBuilder.graph_builder(5)

    simulator.harvest_organs()

    assert 'no patients' in capsys.readouterr().out.lower()
    assert len(simulator.organ_list.organ_list) == 0


def test_harvest_organs_and_allocate_end_to_end(monkeypatch):
    _feed_inputs(monkeypatch, '10', 'n')
    simulator.build_network()
    _feed_inputs(monkeypatch, '20', 'n')
    simulator.generate_patients()

    # harvest count, "print organs?" no, then allocate_organs()'s "press enter" prompt
    _feed_inputs(monkeypatch, '5', 'n', '')
    simulator.harvest_organs()

    # every harvested organ is either transplanted (removed via apply()) or left
    # unmatched and then discarded (organ_list.empty_list() inside AllocationResult.apply)
    assert len(simulator.organ_list.organ_list) == 0


def test_select_strategy_updates_the_selected_strategy(monkeypatch):
    names = list(STRATEGIES.keys())
    target_index = names.index('real_world_circle') + 1
    _feed_inputs(monkeypatch, str(target_index))

    simulator.select_strategy()

    assert simulator.selected_strategy is STRATEGIES['real_world_circle']


def test_select_strategy_rejects_an_out_of_range_index(monkeypatch, capsys):
    original = simulator.selected_strategy
    _feed_inputs(monkeypatch, '9999')

    simulator.select_strategy()

    assert simulator.selected_strategy is original
    assert 'ValueError' in capsys.readouterr().out


def test_reset_network_clears_patients_and_organs_but_keeps_the_network(monkeypatch):
    _feed_inputs(monkeypatch, '5', 'n')
    simulator.build_network()
    _feed_inputs(monkeypatch, '10', 'n')
    simulator.generate_patients()

    simulator.reset_network()

    assert simulator.network is not None
    assert len(simulator.wait_list.wait_list) == 0
    assert len(simulator.organ_list.organ_list) == 0


def test_restart_clears_everything_including_the_network(monkeypatch):
    _feed_inputs(monkeypatch, '5', 'n')
    simulator.build_network()

    simulator.restart()

    assert simulator.network is None
    assert len(simulator.wait_list.wait_list) == 0
    assert len(simulator.organ_list.organ_list) == 0


def test_main_menu_exits_immediately_on_0(monkeypatch, capsys):
    _feed_inputs(monkeypatch, '0')

    simulator.main_menu()

    assert 'Exiting' in capsys.readouterr().out


def test_main_menu_reports_unrecognized_selections_then_exits(monkeypatch, capsys):
    _feed_inputs(monkeypatch, '9', '0')

    simulator.main_menu()

    assert 'Unrecognized menu selection' in capsys.readouterr().out
