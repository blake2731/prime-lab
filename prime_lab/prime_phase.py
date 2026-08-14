from dataclasses import dataclass
from functools import lru_cache
from math import isqrt, pi
from statistics import fmean


@dataclass(frozen=True)
class PrimePhaseState:
    """The phase of one prime cycle at an integer moment."""

    integer: int
    prime: int
    remainder: int
    phase_fraction: float
    angle_radians: float
    angle_degrees: float
    is_zero_crossing: bool
    is_relevant_test_prime: bool
    is_relevant_divisor: bool
    previous_zero: int
    next_zero: int
    steps_to_next_zero: int


@dataclass(frozen=True)
class JointPhasePoint:
    """One state in a two-prime phase projection."""

    integer: int
    first_remainder: int
    second_remainder: int
    first_phase: float
    second_phase: float
    first_zero: bool
    second_zero: bool


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False

    divisor = 3
    while divisor <= isqrt(value):
        if value % divisor == 0:
            return False
        divisor += 2
    return True


@lru_cache(maxsize=8)
def primes_up_to(limit: int) -> tuple[int, ...]:
    """Return all primes less than or equal to ``limit`` using a sieve."""

    if limit < 2:
        return ()

    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"

    for prime in range(2, isqrt(limit) + 1):
        if not sieve[prime]:
            continue
        start = prime * prime
        count = ((limit - start) // prime) + 1
        sieve[start : limit + 1 : prime] = b"\x00" * count

    return tuple(value for value, flag in enumerate(sieve) if flag)


def phase_state(integer: int, prime: int) -> PrimePhaseState:
    """Return the normalized circular phase of ``integer`` modulo ``prime``.

    Phase zero corresponds to a multiple of the prime. The angle uses the
    standard one-turn normalization ``2π * remainder / prime``.
    """

    if integer < 0:
        raise ValueError("integer must be nonnegative")
    if not _is_prime(prime):
        raise ValueError("prime must be prime")

    remainder = integer % prime
    fraction = remainder / prime
    angle_radians = 2 * pi * fraction
    previous_zero = integer - remainder
    next_zero = previous_zero + prime
    relevant_test = prime < integer and prime <= isqrt(integer)
    zero_crossing = remainder == 0

    return PrimePhaseState(
        integer=integer,
        prime=prime,
        remainder=remainder,
        phase_fraction=fraction,
        angle_radians=angle_radians,
        angle_degrees=360.0 * fraction,
        is_zero_crossing=zero_crossing,
        is_relevant_test_prime=relevant_test,
        is_relevant_divisor=relevant_test and zero_crossing,
        previous_zero=previous_zero,
        next_zero=next_zero,
        steps_to_next_zero=next_zero - integer,
    )


def phase_states(integer: int, primes: tuple[int, ...] | list[int]) -> tuple[PrimePhaseState, ...]:
    """Return phase states for a collection of distinct prime cycles."""

    if len(set(primes)) != len(primes):
        raise ValueError("primes must not contain duplicates")
    return tuple(phase_state(integer, prime) for prime in primes)


def synchronized_primes(integer: int, primes: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    """Return selected prime cycles that cross phase zero at ``integer``."""

    return tuple(
        state.prime
        for state in phase_states(integer, primes)
        if state.is_zero_crossing and state.prime < integer
    )


def relevant_divisor_primes(integer: int) -> tuple[int, ...]:
    """Return distinct phase-zero prime divisors needed to classify ``integer``."""

    if integer < 2:
        return ()

    proof_limit = isqrt(integer)
    remaining = integer
    factors: list[int] = []

    for prime in primes_up_to(proof_limit):
        if prime * prime > remaining:
            break
        if remaining % prime != 0:
            continue

        factors.append(prime)
        while remaining % prime == 0:
            remaining //= prime

    if remaining > 1 and remaining <= proof_limit:
        factors.append(remaining)

    return tuple(factors)


def is_prime_from_relevant_phases(integer: int) -> bool:
    """Classify an integer by zero crossings of prime cycles through sqrt(n)."""

    if integer < 2:
        return False
    return not relevant_divisor_primes(integer)


def circular_phase_distance(first: float, second: float) -> float:
    """Return normalized shortest distance between two phases in [0, 1)."""

    a = first % 1.0
    b = second % 1.0
    difference = abs(a - b)
    return min(difference, 1.0 - difference)


def phase_signature_distance(
    first_integer: int,
    second_integer: int,
    primes: tuple[int, ...] | list[int],
) -> float:
    """Mean circular distance between two selected prime-phase signatures."""

    if not primes:
        raise ValueError("at least one prime is required")

    first_states = phase_states(first_integer, primes)
    second_states = phase_states(second_integer, primes)
    return fmean(
        circular_phase_distance(first.phase_fraction, second.phase_fraction)
        for first, second in zip(first_states, second_states, strict=True)
    )


def joint_phase_cycle(first_prime: int, second_prime: int) -> tuple[JointPhasePoint, ...]:
    """Return one complete two-prime phase cycle.

    Distinct primes are coprime, so the joint state repeats after their
    product. Integer zero is included and the repeated endpoint is omitted.
    """

    if not _is_prime(first_prime) or not _is_prime(second_prime):
        raise ValueError("both cycle sizes must be prime")
    if first_prime == second_prime:
        raise ValueError("prime cycles must be distinct")

    period = first_prime * second_prime
    points: list[JointPhasePoint] = []

    for integer in range(period):
        first = phase_state(integer, first_prime)
        second = phase_state(integer, second_prime)
        points.append(
            JointPhasePoint(
                integer=integer,
                first_remainder=first.remainder,
                second_remainder=second.remainder,
                first_phase=first.phase_fraction,
                second_phase=second.phase_fraction,
                first_zero=first.is_zero_crossing,
                second_zero=second.is_zero_crossing,
            )
        )

    return tuple(points)
