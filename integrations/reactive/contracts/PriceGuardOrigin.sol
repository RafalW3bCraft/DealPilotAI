// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

/// @notice Origin event for a catalog price guard.
/// @dev Not deployed. Emitting this event does not move funds.
contract PriceGuardOrigin {
    event PriceGuardTripped(bytes32 indexed sku, uint256 referenceCents, uint256 observedCents);

    function trip(bytes32 sku, uint256 referenceCents, uint256 observedCents) external {
        require(observedCents > referenceCents, "guard not tripped");
        emit PriceGuardTripped(sku, referenceCents, observedCents);
    }
}
