"""Recover sample order without coupling it to DataLoader worker seed draws."""
import hashlib
import itertools

import torch
from torch.utils.data import RandomSampler, Sampler

SCHEMA = "TEXT-RECOVERY-ORDER-v1"


def order_hash(order):
    return hashlib.sha256(order.numpy().astype("<i8", copy=False).tobytes()).hexdigest()


def epoch_order(rows, start_state):
    """Replay the installed RandomSampler, including its exhausted-iterator RNG.

    RandomSampler can draw an unused final permutation. Consuming that draw is
    essential to preserve the next epoch, even though it yields no extra IDs.
    """
    generator = torch.Generator()
    generator.set_state(start_state.cpu())
    iterator = iter(RandomSampler(range(rows), generator=generator))
    order = torch.tensor(list(itertools.islice(iterator, rows)), dtype=torch.int64)
    yielded_state = generator.get_state().clone()
    if list(iterator):
        raise ValueError("Unexpected extra RandomSampler IDs")
    next_state = generator.get_state().clone()
    if len(order) != rows or not torch.equal(order.sort().values, torch.arange(rows)):
        raise ValueError("Sampler does not cover the cohort exactly once")
    return order, yielded_state, next_state


def recover_order(state, rows, batch_size, expected_hash=None):
    order, yielded_state, next_state = epoch_order(rows, state["sampler_start"])
    if state.get("recovery_schema") == SCHEMA:
        if not torch.equal(next_state, state["sampler_next_rng"].cpu()):
            raise ValueError("Recovered next-epoch sampler state differs")
        if state["epoch_order_sha256"] != order_hash(order):
            raise ValueError("Recovered permutation hash differs")
    else:
        # This migration is for the verified later-epoch original checkpoint.
        if state["epoch"] <= 1:
            raise ValueError("Legacy first-epoch recovery needs a separate worker-seed migration")
        if not any(torch.equal(state["loader_rng"].cpu(), s) for s in (yielded_state, next_state)):
            raise ValueError("Legacy checkpoint RNG does not prove this permutation")
    if expected_hash is not None and order_hash(order) != expected_hash:
        raise ValueError("Original frozen permutation hash differs")
    cursor = state["samples_seen"]
    expected_cursor = min(rows, state["step_in_epoch"] * batch_size)
    if cursor != expected_cursor:
        raise ValueError("Checkpoint cursor differs from processed samples")
    return order, next_state, cursor


class FixedSuffixSampler(Sampler):
    def __init__(self):
        self.order = torch.empty(0, dtype=torch.int64)
        self.cursor = 0

    def configure(self, order, cursor=0):
        self.order, self.cursor = order, cursor

    def __iter__(self):
        return iter(self.order[self.cursor:].tolist())

    def __len__(self):
        return len(self.order) - self.cursor


def update_counters(scheduler, updates, skips, scale_before, scale_after):
    """Match the original AMP rule: skipped optimizer steps never decay LR."""
    if scale_after >= scale_before:
        scheduler.step()
        return updates + 1, skips
    return updates, skips + 1
