import numpy as np

from prime_lab.certification import confirmed_prime_mask
from prime_lab.filters import filter_candidates
from prime_lab.residue_analysis import residue_class_summaries


def test_modulo_30_summary_preserves_confirmed_and_unresolved_counts():
    primes = (
        2,
        3,
        5,
    )

    values, survives, eliminated_by = filter_candidates(
        1,
        60,
        primes,
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        primes,
    )

    summaries = residue_class_summaries(
        values,
        survives,
        eliminated_by,
        confirmed,
        active_prime=5,
        modulus=30,
    )

    assert len(summaries) == 30

    assert sum(
        summary.confirmed
        for summary in summaries
    ) == int(
        np.count_nonzero(confirmed)
    )

    assert sum(
        summary.unresolved
        for summary in summaries
    ) == int(
        np.count_nonzero(
            survives
            & ~confirmed
        )
    )

    unresolved_residues = {
        summary.residue
        for summary in summaries
        if summary.unresolved
    }

    assert unresolved_residues == {
        19,
        23,
        29,
    }


def test_modulo_30_marks_exact_prime_eligible_residue_classes():
    values = np.arange(
        1,
        31,
        dtype=np.int64,
    )

    survives = np.ones(
        values.shape,
        dtype=bool,
    )

    eliminated_by = np.zeros(
        values.shape,
        dtype=np.int64,
    )

    confirmed = np.zeros(
        values.shape,
        dtype=bool,
    )

    summaries = residue_class_summaries(
        values,
        survives,
        eliminated_by,
        confirmed,
        active_prime=None,
        modulus=30,
    )

    eligible = tuple(
        summary.residue
        for summary in summaries
        if summary.prime_eligible
    )

    assert eligible == (
        1,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
    )


def test_current_removed_counts_belong_only_to_active_prime():
    primes = (
        2,
        3,
        5,
        7,
    )

    values, survives, eliminated_by = filter_candidates(
        1,
        100,
        primes,
    )

    confirmed = confirmed_prime_mask(
        values,
        survives,
        primes,
    )

    summaries = residue_class_summaries(
        values,
        survives,
        eliminated_by,
        confirmed,
        active_prime=7,
        modulus=30,
    )

    assert sum(
        summary.current_removed
        for summary in summaries
    ) == int(
        np.count_nonzero(
            eliminated_by == 7
        )
    )
