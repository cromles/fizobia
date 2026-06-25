// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./AgentStakingPool.sol";

/// @dev Her OAM ajanı için staking havuzu dağıtır.
contract StakingFactory {
    address public immutable usdc;
    mapping(bytes32 => address) public pools;

    event PoolDeployed(string agentId, address pool);

    constructor(address _usdc) {
        usdc = _usdc;
    }

    function deployPool(string calldata agentId, string calldata tokenSymbol) external returns (address) {
        bytes32 key = keccak256(bytes(agentId));
        require(pools[key] == address(0), "pool exists");
        AgentStakingPool pool = new AgentStakingPool(usdc, agentId, tokenSymbol);
        pools[key] = address(pool);
        emit PoolDeployed(agentId, address(pool));
        return address(pool);
    }

    function getPool(string calldata agentId) external view returns (address) {
        return pools[keccak256(bytes(agentId))];
    }
}
