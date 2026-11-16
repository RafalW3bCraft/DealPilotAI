// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

/// @notice Destination callback for a price-guard reactive contract.
/// @dev Follows https://dev.reactive.network/callback-contracts as fetched on 2026-11-16.
///      The first argument is the reactive sender injected by the callback proxy.
///      This source was not compiled against @reactive and was not deployed.

contract PriceGuardCallback {
    address public immutable callbackProxy;
    address public immutable callbackSender;

    event Handled(address indexed reactive, bytes32 indexed sku, uint256 referenceCents, uint256 observedCents);

    error NotAuthorized();
    error CallbackNotAuthorized();

    modifier onlyServiceProvider() {
        if (msg.sender != callbackProxy) revert NotAuthorized();
        _;
    }

    modifier onlyCallbackSender(address reactive_) {
        if (reactive_ != callbackSender) revert CallbackNotAuthorized();
        _;
    }

    constructor(address callbackProxy_, address callbackSender_) payable {
        callbackProxy = callbackProxy_;
        callbackSender = callbackSender_;
    }

    function onPriceGuard(address reactive_, bytes32 sku, uint256 referenceCents, uint256 observedCents)
        external
        onlyServiceProvider
        onlyCallbackSender(reactive_)
    {
        emit Handled(reactive_, sku, referenceCents, observedCents);
    }
}
