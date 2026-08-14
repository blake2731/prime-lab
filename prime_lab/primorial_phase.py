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


@dataclass(frozen=True)
class DensityConvergencePoint:
    """One checkpoint in a finite density and sieve convergence sweep."""

    exponent: int
    maximum_integer: int
    prime_count: int
    empirical_prime_density: float
    pnt_density: float
    wheel_survivor_fraction: float
    mertens_estimate: float
    proof_cutoff_prime: int
    prime_density_minus_pnt: float
    wheel_minus_prime_density: float
    wheel_to_pnt_ratio: float
    wheel_ratio_error: float
    mertens_absolute_error: float
    mertens_relative_error: float


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


def _prime_sieve(limit: int) -> bytearray:
    """Return primality flags through ``limit`` using Eratosthenes' sieve."""

    if limit < 0:
        raise ValueError("limit must be nonnegative")

    sieve = bytearray(b"\x01") * (limit + 1)
    if limit >= 0:
        sieve[0] = 0
    if limit >= 1:
        sieve[1] = 0

    for prime in range(2, isqrt(limit) + 1):
        if not sieve[prime]:
            continue
        start = prime * prime
        count = ((limit - start) // prime) + 1
        sieve[start : limit + 1 : prime] = b"\x00" * count

    return sieve


@lru_cache(maxsize=4)
def prime_count_up_to(limit: int) -> int:
    """Return pi(limit) using a bounded memory Eratosthenes sieve."""

    if limit < 2:
        return 0
    return int(sum(_prime_sieve(limit)))


def _proof_cutoff_statistics(maximum_integer: int) -> tuple[int, int, float, float]:
    """Return cutoff prime count, cutoff prime, wheel density, and Mertens estimate."""

    proof_limit = isqrt(maximum_integer)
    proof_primes = primes_up_to(proof_limit)
    if not proof_primes:
        raise ValueError("maximum_integer is too small for a prime proof cutoff")

    wheel_survivor_fraction = 1.0
    for prime in proof_primes:
        wheel_survivor_fraction *= (prime - 1) / prime

    proof_cutoff_prime = proof_primes[-1]
    mertens_estimate = exp(-EULER_MASCHERONI) / log(proof_cutoff_prime)
    return (
        len(proof_primes),
        proof_cutoff_prime,
        wheel_survivor_fraction,
        mertens_estimate,
    )


def prime_density_observation(maximum_integer: int) -> PrimeDensityObservation:
    """Compare periodic sieve survivor density with actual prime density.

    The wheel survivor fraction uses every prime not exceeding sqrt(x).
    This is a periodic residue density, while pi(x) / x is an observed
    finite interval density. They are related but are not the same object.
    """

    if maximum_integer < 10:
        raise ValueError("maximum_integer must be at least 10")

    proof_limit = isqrt(maximum_integer)
    (
        proof_prime_count,
        proof_cutoff_prime,
        wheel_survivor_fraction,
        mertens_estimate,
    ) = _proof_cutoff_statistics(maximum_integer)

    count = prime_count_up_to(maximum_integer)
    empirical_density = count / maximum_integer
    pnt_density = 1.0 / log(maximum_integer)

    return PrimeDensityObservation(
        maximum_integer=maximum_integer,
        prime_count=count,
        empirical_prime_density=empirical_density,
        pnt_density=pnt_density,
        proof_limit=proof_limit,
        proof_prime_count=proof_prime_count,
        proof_cutoff_prime=proof_cutoff_prime,
        wheel_survivor_fraction=wheel_survivor_fraction,
        mertens_at_proof_cutoff=mertens_estimate,
        wheel_to_pnt_ratio=wheel_survivor_fraction / pnt_density,
        expected_sqrt_ratio=2.0 * exp(-EULER_MASCHERONI),
    )


def density_convergence_sweep(
    minimum_exponent: int = 2,
    maximum_exponent: int = 7,
) -> tuple[DensityConvergencePoint, ...]:
    """Measure density residuals at powers of ten using one exact prime sieve.

    V1 deliberately bounds the sweep at 10^7 so the complete prime table can
    be recomputed interactively without excessive memory use.
    """

    if minimum_exponent < 2:
        raise ValueError("minimum_exponent must be at least 2")
    if maximum_exponent < minimum_exponent:
        raise ValueError("maximum_exponent must not be smaller than minimum_exponent")
    if maximum_exponent > 7:
        raise ValueError("maximum_exponent must not exceed 7 in the interactive V1 sweep")

    checkpoints = tuple(10**exponent for exponent in range(minimum_exponent, maximum_exponent + 1))
    sieve = _prime_sieve(checkpoints[-1])
    flags = memoryview(sieve)
    expected_ratio = 2.0 * exp(-EULER_MASCHERONI)
    points: list[DensityConvergencePoint] = []

    for exponent, maximum_integer in zip(
        range(minimum_exponent, maximum_exponent + 1),
        checkpoints,
        strict=True,
    ):
        prime_count = int(sum(flags[: maximum_integer + 1]))
        empirical_density = prime_count / maximum_integer
        pnt_density = 1.0 / log(maximum_integer)
        (
            _,
            proof_cutoff_prime,
            wheel_survivor_fraction,
            mertens_estimate,
        ) = _proof_cutoff_statistics(maximum_integer)
        wheel_to_pnt_ratio = wheel_survivor_fraction / pnt_density
        mertens_absolute_error = wheel_survivor_fraction - mertens_estimate

        points.append(
            DensityConvergencePoint(
                exponent=exponent,
                maximum_integer=maximum_integer,
                prime_count=prime_count,
                empirical_prime_density=empirical_density,
                pnt_density=pnt_density,
                wheel_survivor_fraction=wheel_survivor_fraction,
                mertens_estimate=mertens_estimate,
                proof_cutoff_prime=proof_cutoff_prime,
                prime_density_minus_pnt=empirical_density - pnt_density,
                wheel_minus_prime_density=wheel_survivor_fraction - empirical_density,
                wheel_to_pnt_ratio=wheel_to_pnt_ratio,
                wheel_ratio_error=wheel_to_pnt_ratio - expected_ratio,
                mertens_absolute_error=mertens_absolute_error,
                mertens_relative_error=mertens_absolute_error / mertens_estimate,
            )
        )

    return tuple(points)
