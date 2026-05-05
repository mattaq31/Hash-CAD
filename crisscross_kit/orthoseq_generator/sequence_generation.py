import itertools
import random
import time

from tqdm import tqdm

import logging

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())


def revcom(sequence):
    """
    Computes the reverse complement of a DNA sequence.

    :param sequence: Single DNA sequence as a string.
    :type sequence: str

    :returns: Reverse complement of the input sequence as a string.
    :rtype: str
    """
    dna_complement = {"A": "T", "C": "G", "G": "C", "T": "A"}
    return "".join(dna_complement[n] for n in reversed(sequence))


def has_four_consecutive_bases(seq):
    """
    Returns True if the sequence contains four identical consecutive bases
    (e.g., "GGGG", "CCCC", "AAAA", "TTTT").
    """
    return "GGGG" in seq or "CCCC" in seq or "AAAA" in seq or "TTTT" in seq


def sorted_key(seq1, seq2):
    """
    Returns a tuple with the two input sequences sorted alphabetically.
    """
    return (min(seq1, seq2), max(seq1, seq2))


class SequencePairRegistry:
    """
    Stateful generator/registry for DNA sequence pairs.

    It generates random core sequences of fixed length, forms the pair
    (seq, revcom(seq)), applies constraints, and assigns stable integer IDs.
    """

    def __init__(
        self,
        length=7,
        fivep_ext="",
        threep_ext="",
        unwanted_substrings=None,
        apply_unwanted_to="core",
        seed=None,
        preselected_cores=None,
    ):
        self.length = int(length)
        self.fivep_ext = str(fivep_ext)
        self.threep_ext = str(threep_ext)
        self.unwanted_substrings = list(unwanted_substrings) if unwanted_substrings else []

        if apply_unwanted_to not in ("core", "full"):
            raise ValueError('apply_unwanted_to must be "core" or "full"')
        self.apply_unwanted_to = apply_unwanted_to

        self._rng = random.Random(seed)
        self._pair_to_id = {}
        self._id_to_pair = []

        self._bases = ("A", "T", "C", "G")
        if preselected_cores is None:
            self._preselected_cores = None
        else:
            self._preselected_cores = list(preselected_cores)
            for core in self._preselected_cores:
                if len(core) != self.length:
                    raise ValueError(
                        f"preselected core length {len(core)} != registry length {self.length}"
                    )

    def _contains_any_substring(self, seq):
        if not self.unwanted_substrings:
            return False
        for substring in self.unwanted_substrings:
            if substring in seq:
                return True
        return False

    def _random_core(self):
        return "".join(self._rng.choice(self._bases) for _ in range(self.length))

    def _next_preselected_core(self):
        if self._preselected_cores is None or not self._preselected_cores:
            return None
        return self._rng.choice(self._preselected_cores)

    def _make_flanked(self, core_seq):
        core_rc = revcom(core_seq)
        seq = f"{self.fivep_ext}{core_seq}{self.threep_ext}"
        rc_seq = f"{self.fivep_ext}{core_rc}{self.threep_ext}"
        return seq, rc_seq

    def _make_pair(self, core_seq):
        seq, rc_seq = self._make_flanked(core_seq)
        return sorted_key(seq, rc_seq)

    def _is_valid(self, core_seq):
        core_rc = revcom(core_seq)

        if self.apply_unwanted_to == "core":
            if self._contains_any_substring(core_seq):
                return False
            if self._contains_any_substring(core_rc):
                return False
            return True

        seq, rc_seq = self._make_flanked(core_seq)
        if self._contains_any_substring(seq):
            return False
        if self._contains_any_substring(rc_seq):
            return False
        return True

    def sample_pair(self, max_tries=10_000):
        if self._preselected_cores is not None:
            while True:
                core_seq = self._next_preselected_core()
                if core_seq is None:
                    raise RuntimeError("Preselected cores are empty.")

                if not self._is_valid(core_seq):
                    continue

                pair = self._make_pair(core_seq)
                existing_id = self._pair_to_id.get(pair)
                if existing_id is not None:
                    return existing_id, pair

                new_id = len(self._id_to_pair)
                self._pair_to_id[pair] = new_id
                self._id_to_pair.append(pair)
                return new_id, pair

        for _ in range(int(max_tries)):
            core_seq = self._random_core()
            if not self._is_valid(core_seq):
                continue

            pair = self._make_pair(core_seq)
            existing_id = self._pair_to_id.get(pair)
            if existing_id is not None:
                return existing_id, pair

            new_id = len(self._id_to_pair)
            self._pair_to_id[pair] = new_id
            self._id_to_pair.append(pair)
            return new_id, pair

        raise RuntimeError(
            "Could not generate a valid new sequence pair within max_tries. "
            "Relax constraints or increase max_tries."
        )

    def get_pair_by_id(self, pair_id):
        return self._id_to_pair[int(pair_id)]

    def __len__(self):
        return len(self._id_to_pair)


def create_sequence_pairs_pool(length=7, fivep_ext="", threep_ext="", avoid_gggg=True):
    """
    Generates a list of unique DNA sequence pairs with optional flanking sequences.
    """
    bases = ["A", "T", "G", "C"]
    n_mers = ["".join(mer) for mer in itertools.product(bases, repeat=length)]

    unique_pairs_set = set()
    unique_n_mers = []

    for mer in tqdm(n_mers, desc="Generating unique pairs"):
        rc_mer = revcom(mer)
        pair = sorted_key(mer, rc_mer)

        if pair not in unique_pairs_set:
            if avoid_gggg and (
                has_four_consecutive_bases(mer) or has_four_consecutive_bases(rc_mer)
            ):
                continue
            unique_pairs_set.add(pair)
            unique_n_mers.append(pair)

    unique_flanked_n_mers = [
        (f"{fivep_ext}{mer}{threep_ext}", f"{fivep_ext}{rc_mer}{threep_ext}")
        for mer, rc_mer in unique_n_mers
    ]

    return list(enumerate(unique_flanked_n_mers))


def create_seqwalk_sequence_pairs_pool(
    length=7,
    k=3,
    seed=None,
    fivep_ext="",
    threep_ext="",
    alphabet="ACGT",
    avoid_reverse_complements=True,
    gc_lims=None,
    prevented_patterns=None,
    verbose=True,
):
    """
    Generates sequence pairs from SeqWalk and converts them into this module's pair format.
    """
    try:
        from seqwalk import design
    except ImportError as exc:
        raise ImportError(
            "SeqWalk is required for create_seqwalk_sequence_pairs_pool(). "
            "Install it with `pip install seqwalk`."
        ) from exc

    if prevented_patterns is None:
        prevented_patterns = ["AAAA", "CCCC", "GGGG", "TTTT"]

    random_state = None
    if seed is not None:
        random_state = random.getstate()
        random.seed(seed)

    try:
        seqwalk_cores = design.max_size(
            length,
            k,
            alphabet=alphabet,
            RCfree=avoid_reverse_complements,
            GClims=gc_lims,
            prevented_patterns=prevented_patterns,
            verbose=verbose,
        )
    finally:
        if random_state is not None:
            random.setstate(random_state)

    unique_pairs = []
    seen_pairs = set()
    for core_seq in seqwalk_cores:
        pair = sorted_key(
            f"{fivep_ext}{core_seq}{threep_ext}",
            f"{fivep_ext}{revcom(core_seq)}{threep_ext}",
        )
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        unique_pairs.append(pair)

    return list(enumerate(unique_pairs))


def select_subset(sequence_pairs, max_size=200, timeout_s=20):
    """
    Selects a random subset of sequence pairs up to a specified maximum size.
    """
    if isinstance(sequence_pairs, list):
        total = len(sequence_pairs)

        if total > max_size:
            selected = random.sample(sequence_pairs, max_size)
            subset = []
            for index, pair in selected:
                subset.append(pair)
            print(f"Selected random subset of {max_size} pairs from {total} available pairs.")
            return subset

        subset = []
        for index, pair in sequence_pairs:
            subset.append(pair)
        print(f"Using all {total} available pairs (less than or equal to {max_size}).")
        return subset

    if not hasattr(sequence_pairs, "sample_pair"):
        raise TypeError(
            "sequence_pairs must be either a list of (index, (seq, rc_seq)) "
            "or an object with a sample_pair() method."
        )

    start_t = time.time()
    seen_ids = set()
    subset = []

    while len(subset) < max_size:
        if timeout_s is not None and (time.time() - start_t) >= timeout_s:
            print(f"Only {len(subset)} of requested {max_size} found (timeout).")
            logger.info(f"Only {len(subset)} of requested {max_size} found (timeout = {timeout_s}s).")
            return subset

        pair_id, pair = sequence_pairs.sample_pair()
        if pair_id in seen_ids:
            continue

        seen_ids.add(pair_id)
        subset.append(pair)

    print(f"Generated {max_size} unique pairs from registry input.")
    logger.info(f"Selected requested {max_size} sequence pairs.")
    return subset
