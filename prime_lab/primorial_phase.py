from dataclasses import dataclass
from functools import lru_cache
from math import exp, gcd, isqrt, log

from prime_lab.prime_phase import primes_up_to


EULER_MASCHERONI = 0.5772156649015329


@dataclass(frozen=True)
class PrimorialStage:
    """One stage in the progressive activation of prime cycles."""

    stage: int
    prime: int
    primorial: int
    surviving_states: int
    survivor_fraction: float
    eliminated_fraction: float
    mertens_estimate: float
    survivor_to_mertens_ratio: float


@dataclass(frozen=True)
class PrimeDensityObservation:
    """Compare primorial survivor density with observed prime density."""

    maximum_integer: int
    prime_count: int
    empirical_prime_density: float
    pnt_density: float
    proof_limit: int
    proof_prime_count: int
    proof_cutoff_prime: int
    wheel_survivor_fraction: float
    mertens_at_proof_cutoff: float
    wheel_to_pnt_ratio: float
    expected_sqrt_ratio: float


def _first_n_primes(count: int) -> tuple[int, ...]:
    if count < 1:
        raise ValueError("count must be positive")

    limit = 16
    primes = primes_up_to(limit)
    while len(primes) < count:
        limit *= 2
        primes = primes_up_to(limit)
    return primes[:count]


def primorial_stages(count: int) -> tuple[PrimorialStage, ...]:
    """Build exact primorial survivor statistics for the first ``count`` primes.

    At each stage, the total joint residue state count is the primorial
    ``P = product(p)``. States that avoid phase zero on every active prime
    cycle are exactly the residues coprime to P, so their count is
    ``phi(P) = product(p - 1)``.
    """

    primes = _first_n_primes(count)
    primorial = 1
    survivors = 1
    stages: list[PrimorialStage] = []

    for index, prime in enumerate(primes, start=1):
        primorial *= prime
        survivors *= prime - 1
        survivor_fraction = survivors / primorial
        mertens_estimate = exp(-EULER_MASCHERONI) / log(prime)

        stages.append(
            PrimorialStage(
                stage=index,
                prime=prime,
                primorial=primorial,
                surviving_states=survivors,
                survivor_fraction=survivor_fraction,
                eliminated_fraction=1.0 - survivor_fraction,
                mertens_estimate=mertens_estimate,
                survivor_to_mertens_ratio=survivor_fraction / mertens_estimate,
            )
        )

    return tuple(stages)


def survivor_residues(
    primes: tuple[int, ...] | list[int],
    *,
    maximum_modulus: int = 30_030,
) -> tuple[int, tuple[int, ...]]:
    """Return one exact primorial period and its phase zero avoiding residues."""

    if not primes:
        raise ValueError("at least one prime is required")
    if len(set(primes)) != len(primes):
        raise ValueError("primes must be distinct")

    primorial = 1
    for prime in primes:
        if prime not in primes_up_to(prime):
            raise ValueError("all cycle sizes must be prime")
        primorial *= prime

    if primorial > maximum_modulus:
        raise ValueError("primorial exceeds the visualization modulus limit")

    survivors = tuple(
        residue
        for residue in range(1, primorial)
        if gcd(residue, primorial) == 1
    )
    return primorial, survivors


@lru_cache(maxsize=4)
def prime_count_up_to(limit: int) -> int:
    """Return pi(limit) using a bounded memory Eratosthenes sieve."""

    if limit < 2:
        return 0

    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"

    for prime in range(2, isqrt(limit) + 1):
        if not sieve[prime]:
            continue
        start = prime * prime
        count = ((limit - start) // prime) + 1
        sieve[start : limit + 1 : prime] = b"\x00" * count

    return sum(sieve)


def prime_density_observation(maximum_integer: int) -> PrimeDensityObservation:
    """Compare periodic sieve survivor density with actual prime density.

    The wheel survivor fraction uses every prime not exceeding sqrt(x).
    This is a periodic residue density, while pi(x) / x is an observed
    finite interval density. They are related but are not the same object.
    """

    if maximum_integer < 10:
        raise ValueError("maximum_integer must be at least 10")

    proof_limit = isqrt(maximum_integer)
    proof_primes = primes_up_to(proof_limit)
    proof_cutoff_prime = proof_primes[-1]

    wheel_survivor_fraction = 1.0
    for prime in proof_primes:
        wheel_survivor_fraction *= (prime - 1) / prime

    count = prime_count_up_to(maximum_integer)
    empirical_density = count / maximum_integer
    pnt_density = 1.0 / log(maximum_integer)
    mertens_estimate = exp(-EULER_MASCHERONI) / log(proof_cutoff_prime)

    return PrimeDensityObservation(
        maximum_integer=maximum_integer,
        prime_count=count,
        empirical_prime_density=empirical_density,
        pnt_density=pnt_density,
        proof_limit=proof_limit,
        proof_prime_count=len(proof_primes),
        proof_cutoff_prime=proof_cutoff_prime,
        wheel_survivor_fraction=wheel_survivor_fraction,
        mertens_at_proof_cutoff=mertens_estimate,
        wheel_to_pnt_ratio=wheel_survivor_fraction / pnt_density,
        expected_sqrt_ratio=2.0 * exp(-EULER_MASCHERONI),
    )
