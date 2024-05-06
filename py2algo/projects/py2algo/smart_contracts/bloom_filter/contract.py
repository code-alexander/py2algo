# pyright: reportMissingModuleSource=false

from algopy import (
    ARC4Contract,
    Bytes,
    String,
    Txn,
    UInt64,
    arc4,
    itxn,
    op,
    subroutine,
)


@subroutine
def to_index(digest: Bytes) -> UInt64:
    """Maps a hash digest to an index in the range [0, 32_768).

    Args:
        digest (Bytes): The hash digest.

    Returns:
        UInt64: The index.
    """
    return op.extract_uint64(digest, 24) % 32_768


@subroutine
def mint_nft(unit_name: String) -> None:
    """Mints a Bored Algorand Yacht Club NFT.

    Args:
        unit_name (String): The unit name for the asset.
    """
    itxn.AssetConfig(
        total=1,
        decimals=0,
        asset_name="BAYC",
        unit_name=unit_name,
        reserve=Txn.sender,
    ).submit()


class BloomFilter(ARC4Contract):
    """A contract that uses a Bloom filter to ensure unit names are unique."""

    @arc4.abimethod(create="require")
    def new(self, max_supply: UInt64) -> None:
        """Creates a new application and initialises the bloom filter.

        Args:
            max_supply (UInt64): The maximum number of NFTs that can be minted.
        """
        self.max_supply = max_supply
        self.minted = UInt64(0)

    @arc4.abimethod
    def create_bloom_filter(self) -> None:
        """Initialises the bloom filter."""
        _maybe, exists = op.Box.get(b"bloom")
        if not exists:
            op.Box.put(b"bloom", op.bzero(4096))

    @arc4.abimethod
    def buy_nft(self, unit_name: String) -> None:
        """Allows a user to mint anf purchase a BAYC NFT.

        Args:
            unit_name (String): The unit name for the asset.
        """
        assert self.minted < self.max_supply, "Maximum supply reached"

        bloom_filter, exists = op.Box.get(b"bloom")
        assert exists, "Application not bootstrapped"

        h1 = to_index(op.sha512_256(unit_name.bytes))
        h2 = to_index(op.sha3_256(unit_name.bytes))

        assert not (op.getbit(bloom_filter, h1) and op.getbit(bloom_filter, h2)), "Unit name already taken"

        mint_nft(unit_name)
        self.minted += 1

        bloom_filter = op.setbit_bytes(bloom_filter, h1, 1)
        bloom_filter = op.setbit_bytes(bloom_filter, h2, 1)
        op.Box.put(b"bloom", bloom_filter)
