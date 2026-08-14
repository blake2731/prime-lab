from dataclasses import dataclass
from math import isqrt


@dataclass(frozen=True)
class KineticSieveEvent:
    """Mathematical state when the kinetic frontier reaches one integer."""

    value: int
    is_prime: bool
    prime_factors: tuple[int, ...]
    first_eliminating_prime: int | None

    @property
    def is_collision(self) -> bool:
        """Return whether at least two prime trajectories meet here."""

        return len(self.prime_factors) >= 2


@dataclass(frozen=True)
class PrimeTrajectory:
    """A prime's exact sequence of multiples used by the kinetic view."""

    prime: int
    start: int
    stop: int
    landings: tuple[int, ...]


def distinct_prime_factors(value: int) -> tuple[int, ...]:
    """Return the distinct prime factors of a nonnegative integer."""

    if value < 0:
        raise ValueError("value must be nonnegative")

    if value < 2:
        return ()

    remaining = value
    factors: list[int] = []

    divisor = 2

    while divisor <= isqrt(remaining):
        if remaining % divisor == 0:
            factors.append(divisor)

            while remaining % divisor == 0:
                remaining //= divisor

        divisor = 3 if divisor == 2 else divisor + 2

    if remaining > 1 and remaining != value:
        factors.append(remaining)

    return tuple(factors)


def kinetic_sieve_event(value: int) -> KineticSieveEvent:
    """Classify one integer for the kinetic sieve visualization.

    A prime has no earlier prime trajectory landing on it. A composite is
    reached simultaneously by every distinct prime divisor. The smallest
    such divisor remains the first eliminating prime, matching Prime Lab's
    existing sieve ownership convention.
    """

    if value < 0:
        raise ValueError("value must be nonnegative")

    if value < 2:
        return KineticSieveEvent(
            value=value,
            is_prime=False,
            prime_factors=(),
            first_eliminating_prime=None,
        )

    factors = distinct_prime_factors(value)

    if not factors:
        return KineticSieveEvent(
            value=value,
            is_prime=True,
            prime_factors=(),
            first_eliminating_prime=None,
        )

    return KineticSieveEvent(
        value=value,
        is_prime=False,
        prime_factors=factors,
        first_eliminating_prime=factors[0],
    )


def prime_trajectory(
    prime: int,
    stop: int,
    *,
    include_origin: bool = True,
) -> PrimeTrajectory:
    """Return the exact multiples visited by one prime trajectory.

    The kinetic view intentionally visits every multiple of the prime after
    discovery. This differs from an optimized sieve that may begin unique
    elimination work at p squared. Visiting every multiple is what makes
    simultaneous meetings at common multiples visible.
    """

    if prime < 2:
        raise ValueError("prime must be at least 2")

    if distinct_prime_factors(prime):
        raise ValueError("prime must be prime")

    if stop < prime:
        return PrimeTrajectory(
            prime=prime,
            start=prime,
            stop=stop,
            landings=(),
        )

    first = prime if include_origin else 2 * prime

    return PrimeTrajectory(
        prime=prime,
        start=prime,
        stop=stop,
        landings=tuple(
            range(first, stop + 1, prime)
        ),
    )


def kinetic_sieve_events(
    start: int,
    stop: int,
) -> tuple[KineticSieveEvent, ...]:
    """Return frontier events for an inclusive integer interval."""

    if start < 0:
        raise ValueError("start must be nonnegative")

    if stop < start:
        raise ValueError("stop must be greater than or equal to start")

    return tuple(
        kinetic_sieve_event(value)
        for value in range(start, stop + 1)
    )
