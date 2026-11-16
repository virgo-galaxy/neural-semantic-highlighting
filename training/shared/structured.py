"""Optional train-fitted joint BIO/role decoding; never inspect source spelling."""
from __future__ import annotations

import math
import hashlib
import json
import numpy as np

FORMAT = 'nsh-joint-bio-v1'


def parameters_hash(parameters: dict | None) -> str | None:
    if parameters is None:
        return None
    return hashlib.sha256(json.dumps(parameters, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def topology(roles: int):
    states = 1 + roles * 2
    allowed = np.ones((states, states), dtype=bool)
    for role in range(roles):
        inside = 2 + role * 2
        allowed[:, inside] = False
        allowed[[inside - 1, inside], inside] = True
    return allowed


def validate(parameters: dict, schema: dict) -> None:
    if not isinstance(parameters, dict) or parameters.get('format') != FORMAT:
        raise ValueError('Unknown structured decoder format')
    if parameters.get('tokenTypes') != schema['tokenTypes']:
        raise ValueError('Structured decoder role order differs from model')
    for name in ('typeWeight', 'transitionWeight'):
        value = parameters.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError('Invalid structured decoder weight')
    allowed = topology(len(schema['tokenTypes']))
    states = len(allowed)
    transitions, initial = parameters.get('transitions'), parameters.get('initial')
    if (not isinstance(transitions, list) or len(transitions) != states
            or any(not isinstance(row, list) or len(row) != states for row in transitions)
            or not isinstance(initial, list) or len(initial) != states):
        raise ValueError('Invalid structured decoder dimensions')
    def valid(value):
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value <= 0
    for a in range(states):
        if (initial[a] is not None if a > 0 and a % 2 == 0 else not valid(initial[a])):
            raise ValueError('Invalid structured decoder initial state')
        for b in range(states):
            if (not valid(transitions[a][b]) if allowed[a, b] else transitions[a][b] is not None):
                raise ValueError('Invalid structured decoder transition')


def fit(documents: list[dict], schema: dict, *, type_weight: float, transition_weight: float) -> dict:
    """Laplace-smoothed transitions from TRAIN natural Gold, never held-out text."""
    from training.shared.inference import character_map
    allowed = topology(len(schema['tokenTypes']))
    counts = allowed.astype(np.float64)
    initial = np.ones(len(allowed), dtype=np.float64)
    initial[2::2] = 0
    if not documents or any(d.get('stream') != 'natural' for d in documents):
        raise ValueError('Fit structured transitions on natural training documents only')
    for document in documents:
        _, units = character_map(document['source'])
        mapping = {unit: index for index, unit in enumerate(units)}
        states = np.zeros(len(units) - 1, dtype=np.int16)
        for span in document['result']['spans']:
            role = schema['tokenTypes'].index(span['tokenType'])
            a, b = mapping[span['start']], mapping[span['end']]
            states[a:b] = 2 + role * 2
            states[a] = 1 + role * 2
        if len(states):
            initial[states[0]] += 1
            np.add.at(counts, (states[:-1], states[1:]), 1)
    transitions = np.log(np.maximum(counts, 1e-30) / counts.sum(1, keepdims=True))
    start = np.log(np.maximum(initial, 1e-30) / initial.sum())
    result = dict(format=FORMAT, tokenTypes=schema['tokenTypes'], typeWeight=type_weight,
                  transitionWeight=transition_weight,
                  transitions=[[float(value) if allowed[a, b] else None for b, value in enumerate(row)]
                               for a, row in enumerate(transitions)],
                  initial=[None if a > 0 and a % 2 == 0 else float(value) for a, value in enumerate(start)])
    validate(result, schema)
    return result


def ranges(boundary, token, parameters: dict) -> list[tuple[int, int, int]]:
    """Return character-index ranges and role IDs from neural logits alone."""
    count, roles = token.shape
    if not count:
        return []
    states = 1 + roles * 2
    # Float64 matches JS Number and avoids accumulated score cancellation.
    b = boundary.numpy().astype(np.float64)
    t = token.numpy().astype(np.float64)
    emissions = np.empty((count, states), dtype=np.float64)
    emissions[:, 0] = b[:, 0]
    types = (t - t.max(1, keepdims=True)) * parameters['typeWeight']
    emissions[:, 1::2] = b[:, 1:2] + types
    emissions[:, 2::2] = b[:, 2:3] + types
    weight = parameters['transitionWeight']
    transitions = np.array([[value * weight if value is not None else -np.inf for value in row]
                            for row in parameters['transitions']])
    score = emissions[0] + np.array([value * weight if value is not None else -np.inf
                                     for value in parameters['initial']])
    back = np.zeros((count, states), dtype=np.int16)
    columns = np.arange(states)
    for index in range(1, count):
        values = score[:, None] + transitions
        best = values.argmax(0)
        back[index] = best
        score = values[best, columns] + emissions[index]
    state = int(score.argmax())
    path = np.empty(count, dtype=np.int16)
    for index in range(count - 1, -1, -1):
        path[index] = state
        state = int(back[index, state])
    result, begin, role = [], None, None
    for index, state in enumerate(path):
        if state == 0 or state % 2:
            if begin is not None:
                result.append((begin, index, role))
            begin = index if state else None
            role = (int(state) - 1) // 2 if state else None
    if begin is not None:
        result.append((begin, count, role))
    return result
