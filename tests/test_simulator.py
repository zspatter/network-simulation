"""
execute/simulator.py is the interactive console simulator. State lives on a
SimulatorSession instance (network, wait_list, organ_list, selected_strategy),
and each menu method calls input() one or more times. Tests create a fresh
session per test and feed canned input() responses via monkeypatch, rather than
driving the real console or mutating shared module state.
"""
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import simulator  # noqa: E402

from organflow.allocation import STRATEGIES  # noqa: E402
from organflow.GraphBuilder import GraphBuilder  # noqa: E402


def _feed_inputs(monkeypatch, *responses):
    """Makes successive input() calls return each of `responses` in order."""
    iterator = iter(responses)
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(iterator))


def test_build_network_creates_a_network_of_the_requested_size(monkeypatch):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '5', 'n')

    session.build_network()

    assert session.network is not None
    assert len(session.network.network_dict) == 5


def test_build_network_handles_invalid_node_count(monkeypatch, capsys):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, 'not a number')

    session.build_network()

    assert session.network is None
    assert 'ValueError' in capsys.readouterr().out


def test_build_network_prompts_before_clearing_an_existing_network(monkeypatch):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '5', 'n')
    session.build_network()
    assert session.network is not None

    # a second call with an existing network asks to confirm clearing first
    _feed_inputs(monkeypatch, 'n')
    session.build_network()
    assert len(session.network.network_dict) == 5  # unchanged - declined to clear


def test_generate_patients_requires_a_network_first(capsys):
    session = simulator.SimulatorSession()

    session.generate_patients()

    out = capsys.readouterr().out
    assert 'no network' in out
    assert len(session.wait_list.wait_list) == 0


def test_generate_patients_populates_the_wait_list(monkeypatch):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '5', 'n')
    session.build_network()

    _feed_inputs(monkeypatch, '10', 'n')
    session.generate_patients()

    assert len(session.wait_list.wait_list) == 10


def test_harvest_organs_requires_a_network(capsys):
    session = simulator.SimulatorSession()

    session.harvest_organs()

    assert 'no network' in capsys.readouterr().out.lower()
    assert len(session.organ_list.organ_list) == 0


def test_harvest_organs_requires_patients_on_the_wait_list(capsys):
    session = simulator.SimulatorSession()
    session.network = GraphBuilder.graph_builder(5)

    session.harvest_organs()

    assert 'no patients' in capsys.readouterr().out.lower()
    assert len(session.organ_list.organ_list) == 0


def test_harvest_organs_and_allocate_end_to_end(monkeypatch):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '10', 'n')
    session.build_network()
    _feed_inputs(monkeypatch, '20', 'n')
    session.generate_patients()

    # harvest count, "print organs?" no, then allocate_organs()'s "press enter" prompt
    _feed_inputs(monkeypatch, '5', 'n', '')
    session.harvest_organs()

    # every harvested organ is either transplanted (removed via apply()) or left
    # unmatched and then discarded (organ_list.empty_list() inside AllocationResult.apply)
    assert len(session.organ_list.organ_list) == 0


def test_select_strategy_updates_the_selected_strategy(monkeypatch):
    session = simulator.SimulatorSession()
    names = list(STRATEGIES.keys())
    target_index = names.index('real_world_circle') + 1
    _feed_inputs(monkeypatch, str(target_index))

    session.select_strategy()

    assert session.selected_strategy is STRATEGIES['real_world_circle']


def test_select_strategy_rejects_an_out_of_range_index(monkeypatch, capsys):
    session = simulator.SimulatorSession()
    original = session.selected_strategy
    _feed_inputs(monkeypatch, '9999')

    session.select_strategy()

    assert session.selected_strategy is original
    assert 'ValueError' in capsys.readouterr().out


def test_reset_network_clears_patients_and_organs_but_keeps_the_network(monkeypatch):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '5', 'n')
    session.build_network()
    _feed_inputs(monkeypatch, '10', 'n')
    session.generate_patients()

    session.reset_network()

    assert session.network is not None
    assert len(session.wait_list.wait_list) == 0
    assert len(session.organ_list.organ_list) == 0


def test_restart_clears_everything_including_the_network(monkeypatch):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '5', 'n')
    session.build_network()

    session.restart()

    assert session.network is None
    assert len(session.wait_list.wait_list) == 0
    assert len(session.organ_list.organ_list) == 0


def test_main_menu_exits_immediately_on_0(monkeypatch, capsys):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '0')

    session.main_menu()

    assert 'Exiting' in capsys.readouterr().out


def test_main_menu_reports_unrecognized_selections_then_exits(monkeypatch, capsys):
    session = simulator.SimulatorSession()
    _feed_inputs(monkeypatch, '9', '0')

    session.main_menu()

    assert 'Unrecognized menu selection' in capsys.readouterr().out
