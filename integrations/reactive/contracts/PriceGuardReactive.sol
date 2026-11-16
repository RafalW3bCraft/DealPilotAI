// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

/// @notice Reactive contract for a PriceGuardTripped origin event.
/// @dev Follows https://dev.reactive.network/reactive-contracts as fetched on 2026-11-16.
///      REACTIVE_IGNORE is the value published in Reactive-Network/reactive-lib.
///      This source was not compiled against @reactive and was not deployed.
///      No testnet transaction hash exists for it.

interface IPriceGuardSystem {
    struct CallbackConfiguration_V_1_0 {
        uint256 chainId;
        address recipient;
        uint64 gasLimit;
        bytes payload;
    }

    function subscribe(
        uint256 chainId_,
        address contract_,
        uint256 topic0_,
        uint256 topic1_,
        uint256 topic2_,
        uint256 topic3_
    ) external;

    function requestCallbackV_1_0(CallbackConfiguration_V_1_0 memory config_) external;
}

contract PriceGuardReactive {
    uint256 internal constant REACTIVE_IGNORE =
        0xa65f96fc951c35ead38878e0f0b7a3c744a6f5ccc1476b313353ce31712313ad;
    address internal constant SYSTEM = 0x8888888888888888888888888888888888888888;
    uint64 internal constant CALLBACK_GAS_LIMIT = 1000000;

    uint256 private immutable originChainId;
    address private immutable originContract;
    uint256 private immutable topic0;
    uint256 private destinationChainId;
    address private recipient;

    error NotAuthorized();

    modifier onlySystem() {
        if (msg.sender != SYSTEM) revert NotAuthorized();
        _;
    }

    constructor(uint256 originChainId_, address originContract_, uint256 topic0_) payable {
        originChainId = originChainId_;
        originContract = originContract_;
        topic0 = topic0_;
        IPriceGuardSystem(SYSTEM).subscribe(
            originChainId_,
            originContract_,
            topic0_,
            REACTIVE_IGNORE,
            REACTIVE_IGNORE,
            REACTIVE_IGNORE
        );
    }

    function setDestination(uint256 destinationChainId_, address recipient_) external {
        destinationChainId = destinationChainId_;
        recipient = recipient_;
    }

    function react(
        uint256 chainId_,
        address contract_,
        uint256 topic0_,
        uint256 topic1_,
        uint256 opcode_,
        bytes calldata data_
    ) external onlySystem {
        if (chainId_ != originChainId || contract_ != originContract || topic0_ != topic0 || opcode_ != 2) {
            return;
        }
        (uint256 referenceCents, uint256 observedCents) = abi.decode(data_, (uint256, uint256));
        if (observedCents <= referenceCents || recipient == address(0)) {
            return;
        }
        bytes memory payload = abi.encodeWithSignature(
            "onPriceGuard(address,bytes32,uint256,uint256)",
            address(0),
            bytes32(topic1_),
            referenceCents,
            observedCents
        );
        IPriceGuardSystem(SYSTEM).requestCallbackV_1_0(
            IPriceGuardSystem.CallbackConfiguration_V_1_0({
                chainId: destinationChainId,
                recipient: recipient,
                gasLimit: CALLBACK_GAS_LIMIT,
                payload: payload
            })
        );
    }
}
